"""Display-only previews. Original and quality-filtered pixels stay separate.

No preview changes photometry, scientific FITS or source quality decisions.
"""
import hashlib
import json
import uuid

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image, ImageDraw
from reproject import reproject_interp

from backend import store
from backend.science import BAD_FLAGS, download_path, stretch_rgba, replace_ready_file


def save_png(image, path):
    temp = path.with_name(path.stem+'.'+uuid.uuid4().hex+'.tmp')
    try:
        image.save(temp, format='PNG')
        replace_ready_file(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def original_pixels(manifest, frame):
    folder = store.ROOT/'analyses'/manifest['id']
    cached = folder/f"{frame['id']}.display.npz"
    if cached.exists():
        with np.load(cached) as data:
            return data['image'], data['warned']
    search = manifest['search']
    path = download_path(frame, SkyCoord(search['ra'], search['dec'], unit='deg'), search['fov_arcmin'])
    if not path.exists():
        raise ValueError('Brak oryginalnego FITS w pamięci serwera. Wybierz widok po kontroli jakości lub przygotuj zdjęcia ponownie.')
    n = manifest['pixels']
    target = WCS(manifest['wcs'])
    with fits.open(path, memmap=False) as hdus:
        spatial = WCS(hdus['IMAGE'].header)
        image, coverage = reproject_interp((hdus['IMAGE'].data.astype(float), spatial), target, shape_out=(n,n))
        image[coverage < .99] = np.nan
        flags, _ = reproject_interp((hdus['FLAGS'].data.astype(float), spatial), target, shape_out=(n,n), order='nearest-neighbor')
        flags = np.nan_to_num(flags).astype(np.uint32)
    badmask = sum(1 << bit for name, bit in frame['flag_definitions'].items() if name in BAD_FLAGS)
    warned = ((flags & badmask) != 0) & np.isfinite(image)
    temp = cached.with_name(cached.stem+'.'+uuid.uuid4().hex+'.tmp.npz')
    try:
        np.savez_compressed(temp, image=image, warned=warned)
        replace_ready_file(temp, cached)
    finally:
        temp.unlink(missing_ok=True)
    return image, warned


def display_limits(arrays, mode):
    values = np.concatenate([a[np.isfinite(a)] for a in arrays])
    if not values.size:
        raise ValueError('Brak zarejestrowanych pikseli w tym polu.')
    if mode == 'full':
        low, high = float(np.min(values)), float(np.max(values))
    else:
        low, high = np.percentile(values, [.5, 99 if mode == 'faint' else 99.7])
    return float(low), float(high if high > low else low+1)


def make_previews(manifest, quality='all', range_mode='standard', frame_ids=None):
    settings = dict(analysis_id=manifest['id'], quality=quality, range_mode=range_mode, version='display-1')
    selected = manifest['frames']
    if frame_ids is not None:
        if not frame_ids or not set(frame_ids) <= {frame['id'] for frame in selected}:
            raise ValueError('Wybierz przygotowane klatki tej analizy.')
        settings['frame_ids'] = sorted(set(frame_ids))
        selected = [frame for frame in selected if frame['id'] in frame_ids]
    key = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
    existing = store.get('preview', key)
    if existing:
        return existing
    arrays, warned_masks = [], []
    folder = store.ROOT/'analyses'/manifest['id']
    for frame in selected:
        if quality == 'all':
            image, warned = original_pixels(manifest, frame)
        else:
            image = fits.getdata(folder/f"{frame['id']}.fits").astype(float)
            warned = np.zeros(image.shape, dtype=bool)
        arrays.append(image)
        warned_masks.append(warned)
    low, high = display_limits(arrays, range_mode)
    output = store.ROOT/'previews'/key
    output.mkdir(parents=True, exist_ok=True)
    frames = []
    for frame, array, warned in zip(selected, arrays, warned_masks):
        save_png(Image.fromarray(stretch_rgba(array, low, high)[::-1]), output/f"{frame['id']}.png")
        # Separate outlines leave the underlying pixel intensity untouched.
        scale = 4
        overlay = Image.new('RGBA', (array.shape[1]*scale, array.shape[0]*scale))
        painter = ImageDraw.Draw(overlay)
        for y, x in zip(*np.where(warned[::-1])):
            painter.rectangle((int(x)*scale, int(y)*scale, (int(x)+1)*scale-1, (int(y)+1)*scale-1), outline=(255,177,76,220), width=1)
        save_png(overlay, output/f"{frame['id']}-quality.png")
        frames.append(dict(id=frame['id'], image=f"/api/previews/{key}/{frame['id']}.png",
                           quality_image=f"/api/previews/{key}/{frame['id']}-quality.png",
                           display_coverage=float(np.isfinite(array).mean()), warned_fraction=float(warned.mean())))
    result = dict(id=key, **settings, frames=frames, display=dict(low=low, high=high, common_scale=True),
                  note='Podgląd nie zmienia masek jakości ani danych używanych do pomiarów. Braków nie uzupełniono.')
    store.put('preview', key, result)
    return result
