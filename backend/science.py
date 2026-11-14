"""Qualitative image comparison; never reports detection significance or photometry."""
import hashlib
import json
import time
import shutil
from datetime import datetime, timezone

import httpx
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image
from reproject import reproject_interp

from backend.archive import safe_archive_url
from backend.store import ROOT, put

PIPELINE_VERSION = "0.2.0"
BAD_FLAGS = {"OVERFLOW", "SUR_ERROR", "NONFUNC", "MISSING_DATA", "HOT", "COLD", "NONLINEAR"}

def replace_ready_file(source, destination):
    # Windows readers/scanners can briefly hold the previous snapshot open.
    # Keep it intact until the complete replacement can be installed.
    for attempt in range(6):
        try:
            source.replace(destination)
            return
        except PermissionError:
            if attempt == 5:
                raise
            time.sleep(.05 * 2**attempt)

def output_wcs(ra, dec, fov_arcmin, pixels):
    w = WCS(naxis=2)
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.crval = [ra, dec]
    w.wcs.crpix = [(pixels+1)/2, (pixels+1)/2]
    w.wcs.cdelt = [-fov_arcmin/60/pixels, fov_arcmin/60/pixels]
    return w

def stretch_rgba(data, low, high):
    valid = np.isfinite(data)
    scaled = np.zeros(data.shape, dtype=float)
    scaled[valid] = np.arcsinh(8*np.clip((data[valid]-low)/(high-low), 0, 1))/np.arcsinh(8)
    gray = np.uint8(np.round(scaled*255))
    return np.dstack([gray, gray, gray, valid.astype(np.uint8)*255])

def cutout_parameters(obs, center, fov):
    size = float(obs.get('cutout_fov_arcmin', fov))
    if not np.isfinite(size) or not 2 <= size <= 30:
        raise ValueError('Native cutout size must be between 2 and 30 arcmin.')
    return dict(center=f"{center.ra.deg},{center.dec.deg}d", size=str(size/60))


def download_path(obs, center, fov):
    url = safe_archive_url(obs["url"])
    params = cutout_parameters(obs, center, fov)
    key = hashlib.sha256((url+json.dumps(params, sort_keys=True)).encode()).hexdigest()
    cache = ROOT / "fits"
    cache.mkdir(exist_ok=True)
    return cache / f"{key}.fits"


def download(obs, center, fov, *, timeout=120, attempts=3):
    url = safe_archive_url(obs["url"])
    params = cutout_parameters(obs, center, fov)
    path = download_path(obs, center, fov)
    if not path.exists():
        temp = path.with_suffix(".part")
        try:
            for attempt in range(attempts):
                try:
                    with httpx.stream("GET", url, params=params, timeout=timeout, follow_redirects=False) as r:
                        r.raise_for_status()
                        size = 0
                        with temp.open("wb") as output:
                            for chunk in r.iter_bytes():
                                size += len(chunk)
                                if size > 80*1024*1024:
                                    raise ValueError("Produkt przekracza limit 80 MB.")
                                output.write(chunk)
                    break
                except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                    retryable = not isinstance(exc,httpx.HTTPStatusError) or exc.response.status_code in (429,500,502,503,504)
                    if attempt == attempts-1 or not retryable:
                        raise
                    time.sleep(2*(attempt+1))
            with fits.open(temp) as hdus:
                if "IMAGE" not in hdus or "WCS-WAVE" not in hdus:
                    raise ValueError("Archiwum nie zwróciło wymaganego FITS.")
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)
    return path

def read_frame(path, coord, target_wcs, pixels):
    with fits.open(path, memmap=False) as hdus:
        header = hdus["IMAGE"].header
        spatial = WCS(header)
        spectral = WCS(header, fobj=hdus, key="W")
        spectral.sip = None
        x, y = spatial.world_to_pixel(coord)
        wavelength, bandwidth = spectral.pixel_to_world(x, y)
        wl, bw = float(wavelength.to_value(u.um)), float(bandwidth.to_value(u.um))
        if not (np.isfinite(wl) and np.isfinite(bw) and bw > 0):
            raise ValueError("Brak informacji o paśmie w centrum pola.")
        data = hdus["IMAGE"].data.astype(float)
        flags = hdus["FLAGS"].data.astype(np.uint32)
        flag_header = hdus["FLAGS"].header
        bitmask = 0
        definitions = {}
        for key in flag_header:
            if key.startswith("MSKN") and key[4:].isdigit():
                bit = int(key[4:])
                name = str(flag_header[key]).strip()
                definitions[name] = bit
                if name in BAD_FLAGS:
                    bitmask |= 1 << bit
        data[(flags & bitmask) != 0] = np.nan
        image, footprint = reproject_interp((data, spatial), target_wcs, shape_out=(pixels,pixels), order="bilinear")
        image[footprint < .99] = np.nan
        # Flag words are sampled with nearest-neighbour interpolation only.
        projected_flags, _ = reproject_interp((flags.astype(float), spatial), target_wcs, shape_out=(pixels,pixels), order="nearest-neighbor")
        projected_flags = np.nan_to_num(projected_flags).astype(np.uint32)
        yy, xx = np.indices((pixels,pixels))
        sky = target_wcs.pixel_to_world(xx, yy)
        sx, sy = spatial.world_to_pixel(sky)
        wl_map, bw_map = spectral.pixel_to_world(sx, sy)
        return image, projected_flags, wl_map.to_value(u.um), bw_map.to_value(u.um), dict(
            wavelength_um=wl, bandwidth_um=bw, unit=header.get("BUNIT", "unknown"),
            coverage=float(np.isfinite(image).mean()), flag_definitions=definitions,
            masked_flags=sorted(BAD_FLAGS & definitions.keys()),
            processing_version=str(hdus[0].header.get("VERSION", "unknown")),
            detector=str(header.get("DETECTOR", "unknown")),
        )

def build_analysis(id, search, observation_ids, previous=None, selection=None, initial_failures=None, workspace=None):
    folder = ROOT / "analyses" / id
    folder.mkdir(parents=True, exist_ok=True)
    try:
        overrides = {r['id']: r for r in (selection or {}).get('candidates', [])}
        # Larger native cutouts do not change the requested output sky geometry.
        selected = sorted([dict(o, **({'cutout_fov_arcmin': overrides[o['id']]['cutout_fov_arcmin']}
                           if o['id'] in overrides and 'cutout_fov_arcmin' in overrides[o['id']] else {}))
                           for o in search["observations"] if o["id"] in observation_ids], key=lambda o: o['mjd'])
        pixels = max(32, int(np.ceil(search["fov_arcmin"]*60/6.2)))
        wcs = output_wcs(search["ra"], search["dec"], search["fov_arcmin"], pixels)
        coord = SkyCoord(search["ra"], search["dec"], unit="deg")
        frames, arrays, failures = [], [], list(initial_failures or [])
        reusable = {f['id']: f for f in previous['frames']} if previous else {}
        for i, obs in enumerate(selected):
            put("job", id, dict(id=id, status="running", completed=i, total=len(selected), message=f"Pobieranie i wyrównanie {i+1}/{len(selected)}"))
            try:
                if obs['id'] in reusable:
                    prior_folder = ROOT / 'analyses' / previous['id']
                    if all((prior_folder / f"{obs['id']}.{suffix}").exists() for suffix in ('npz', 'fits')):
                        for suffix in ('npz', 'fits'):
                            if prior_folder != folder:
                                shutil.copyfile(prior_folder / f"{obs['id']}.{suffix}", folder / f"{obs['id']}.{suffix}")
                        display_cache = prior_folder / f"{obs['id']}.display.npz"
                        if prior_folder != folder and display_cache.exists():
                            shutil.copyfile(display_cache, folder / display_cache.name)
                        array = fits.getdata(folder / f"{obs['id']}.fits").astype(float)
                        frames.append(dict(reusable[obs['id']], image=f"/api/analyses/{id}/frames/{obs['id']}.png"))
                        arrays.append(array)
                        continue
                put('job', id, dict(id=id, status='running', completed=i, total=len(selected), message=f'Pobieranie FITS {i+1}/{len(selected)} (z cache, jeśli dostępny)'))
                path = download(obs, coord, search["fov_arcmin"])
                put('job', id, dict(id=id, status='running', completed=i, total=len(selected), message=f'Wyrównywanie obrazu {i+1}/{len(selected)}'))
                array, flags, wlmap, bwmap, metadata = read_frame(path, coord, wcs, pixels)
                if not np.isfinite(array).any():
                    raise ValueError("Brak ważnego pokrycia w wybranym polu.")
                frame_id = obs["id"]
                np.savez_compressed(folder / f"{frame_id}.npz", flags=flags, wavelength=wlmap, bandwidth=bwmap, valid=np.isfinite(array))
                output_header = wcs.to_header()
                output_header["BUNIT"] = metadata["unit"]
                output_header["ORIGIN"] = "SPHEREx comparison pipeline " + PIPELINE_VERSION
                output_header["HISTORY"] = "Bilinear reprojection; selected bad flags masked; ZODI not subtracted."
                fits.PrimaryHDU(array.astype(np.float32), header=output_header).writeto(folder / f"{frame_id}.fits", overwrite=True)
                frames.append(dict(**obs, **metadata, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), image=f"/api/analyses/{id}/frames/{frame_id}.png"))
                arrays.append(array)
            except Exception as exc:
                failures.append(dict(observation=obs["id"], error=f"{type(exc).__name__}: {exc}"))
        if not frames:
            raise ValueError(f"Nie uzyskano żadnej poprawnej klatki. Ponów przygotowanie lub wybierz inne obserwacje. Szczegóły: {failures}")
        units = {f["unit"] for f in frames}
        if len(units) != 1:
            raise ValueError("Niezgodne jednostki obrazów; porównanie wstrzymane.")
        values = np.concatenate([a[np.isfinite(a)] for a in arrays])
        low, high = np.percentile(values, [1,99.7])
        if high <= low:
            high = low + 1
        for frame, array in zip(frames, arrays):
            put('job', id, dict(id=id, status='running', completed=len(selected), total=len(selected), message='Tworzenie podglądów ze wspólną skalą jasności'))
            # Canvas uses top-left origin; FITS uses lower-left. Reverse rows for PNG.
            temp = folder / f"{frame['id']}.tmp"
            Image.fromarray(stretch_rgba(array, low, high)[::-1]).save(temp, format='PNG')
            replace_ready_file(temp, folder / f"{frame['id']}.png")
            frame['image'] += '?v=final'
        from backend.orientation import footprint
        manifest = dict(id=id, schema_version=2, pipeline_version=PIPELINE_VERSION,
                        created_at=datetime.now(timezone.utc).isoformat(), search=search,
                        provisional=False, revision=(previous or {}).get('revision', 0)+1,
                        frames=frames, failures=failures, pixels=pixels, wcs=dict(wcs.to_header()), footprint=footprint(wcs, pixels),
                        processing=dict(background="not_subtracted", psf="not_matched", uncertainty="not_propagated_to_reprojected_images", interpolation="bilinear"),
                        display=dict(low=float(low), high=float(high), stretch="asinh", common_scale=True),
                        limitations=["Porównanie jakościowe. Bez pomiaru ruchu, fotometrii i dopasowania PSF.",
                                      "Zgodność długości fal należy sprawdzić w miejscu badanego źródła.",
                                      "Tło zodiakalne pozostawiono w obrazach. Nie wykonywano odejmowania tła.",
                                      "Interpolacja biliniowa; wariancja nie jest używana do wnioskowania statystycznego."],
                        acknowledgement="This publication makes use of data products from the Spectro-Photometer for the History of the Universe, Epoch of Reionization and Ices Explorer (SPHEREx), which is a joint project of the Jet Propulsion Laboratory and the California Institute of Technology, and is funded by the National Aeronautics and Space Administration.")
        if selection is not None:
            manifest['selection'] = selection
        if workspace is not None:
            manifest['workspace'] = workspace
        temp_manifest = folder / 'manifest.tmp'
        temp_manifest.write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding='utf-8')
        replace_ready_file(temp_manifest, folder / 'manifest.json')
        put("analysis", id, manifest)
        put("job", id, dict(id=id, status="complete", completed=len(selected), total=len(selected), message="Porównanie gotowe"))
    except Exception as exc:
        put("job", id, dict(id=id, status="failed", message=str(exc)))
