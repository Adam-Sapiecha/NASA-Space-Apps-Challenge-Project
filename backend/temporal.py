"""Bounded qualitative operations, fixed weights and local spectral masks."""
import hashlib
import json
from datetime import datetime, timezone

import numpy as np
from astropy.io import fits
from PIL import Image

from backend import store
from backend.science import PIPELINE_VERSION, stretch_rgba


def combine(arrays, wavelengths, bandwidths, weights, operation):
    values = np.array(arrays)
    wl, bw = np.array(wavelengths), np.array(bandwidths)
    # Every pair must pass at this pixel. No per-pixel renormalization of weights.
    valid = np.all(np.isfinite(values) & np.isfinite(wl) & np.isfinite(bw) & (bw > 0), axis=0)
    for i in range(len(values)):
        for j in range(i):
            valid &= np.abs(wl[i]-wl[j]) <= np.minimum(bw[i], bw[j])/2
    if operation == 'difference':
        result = values[0]-values[1]
    else:
        result = np.sum(values*np.array(weights)[:, None, None], axis=0)/sum(weights)
    result[~valid] = np.nan
    return result


def product(manifest, ids, weights, operation, max_hours):
    lookup = {f['id']: f for f in manifest['frames']}
    if len(ids) != len(set(ids)) or not set(ids) <= lookup.keys():
        raise ValueError('Wybierz różne klatki zapisanej analizy.')
    frames = [lookup[id] for id in ids]
    if len({f['unit'] for f in frames}) != 1:
        raise ValueError('Niezgodne jednostki.')
    if len(weights) != len(ids) or not all(np.isfinite(w) and 0 < w <= 100 for w in weights):
        raise ValueError('Każda klatka wymaga stałej wagi większej od 0 i nie większej od 100.')
    if operation == 'difference' and len(ids) != 2:
        raise ValueError('Różnica wymaga dokładnie dwóch klatek; kolejność to A−B.')
    if operation == 'difference' and weights != [1, 1]:
        raise ValueError('Podgląd A−B wymaga wag 1 i 1; ręczne wagi dotyczą składania.')
    if operation == 'stack' and (max(f['mjd'] for f in frames)-min(f['mjd'] for f in frames))*24 > max_hours:
        raise ValueError('Przekroczono wybrane okno składania. Ogranicz daty; składanie może rozmyć ruch.')
    arrays, wavelengths, bandwidths = [], [], []
    folder = store.ROOT/'analyses'/manifest['id']
    for frame in frames:
        arrays.append(fits.getdata(folder/f"{frame['id']}.fits").astype(float))
        with np.load(folder/f"{frame['id']}.npz") as data:
            wavelengths.append(data['wavelength'])
            bandwidths.append(data['bandwidth'])
    image = combine(arrays, wavelengths, bandwidths, weights, operation)
    values = image[np.isfinite(image)]
    if not values.size:
        raise ValueError('Brak wspólnego ważnego pokrycia o zbliżonych lokalnych pasmach.')
    settings = dict(analysis_id=manifest['id'], frame_ids=ids, weights=weights, operation=operation,
                    max_hours=max_hours, pipeline_version=PIPELINE_VERSION)
    id = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()
    existing = store.get('product', id)
    if existing:
        return existing
    output = store.ROOT/'products'/id
    output.mkdir(parents=True, exist_ok=True)
    if operation == 'difference':
        high = max(float(np.percentile(np.abs(values), 99)), 1e-12)
        t = np.nan_to_num(np.clip(image/high, -1, 1))
        rgb = np.stack([1+np.minimum(t, 0), 1-np.abs(t), 1-np.maximum(t, 0)], axis=-1)
        rgba = np.dstack([(rgb*255).astype(np.uint8), np.isfinite(image).astype(np.uint8)*255])
        low = -high
    else:
        low, high = manifest['display']['low'], manifest['display']['high']
        rgba = stretch_rgba(image, low, high)
    Image.fromarray(rgba[::-1]).save(output/'preview.png')
    header = fits.Header(manifest['wcs'])
    header['BUNIT'] = frames[0]['unit']
    header['HISTORY'] = 'Qualitative operation. No PSF matching. No significance estimate.'
    fits.PrimaryHDU(image.astype(np.float32), header=header).writeto(output/'image.fits', overwrite=True)
    result = dict(id=id, **settings, created_at=datetime.now(timezone.utc).isoformat(),
                  image=f'/api/products/{id}/preview.png', coverage=float(np.isfinite(image).mean()),
                  date_start=min(f['date'] for f in frames), date_end=max(f['date'] for f in frames),
                  display=dict(low=low, high=high, unit=frames[0]['unit'], common_scale=operation=='stack'),
                  inputs=[dict(id=f['id'], sha256=f['sha256'], date=f['date']) for f in frames],
                  output_sha256=hashlib.sha256((output/'image.fits').read_bytes()).hexdigest(),
                  limitations=['Podgląd jakościowy. Bez dopasowania PSF, bez modelu niepewności i bez istotności statystycznej.',
                               'Tło nie jest dopasowane; różnice tła lub rejestracji mogą imitować ruch i zmienność.',
                               'Próg lokalnych pasm jest heurystyką podglądu z WCS-WAVE.',
                               'Tylko wspólne pokrycie wszystkich składników; stałe wagi, bez uzupełniania braków.'])
    (output/'manifest.json').write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    store.put('product', id, result)
    return result
