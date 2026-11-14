"""Bounded, target-local observation selection. Never ranks on measured flux.

Flags, apertures and background use the same gates as native photometry. A
matching WCS-WAVE band is only a browsing heuristic, not a calibrated response.
"""
import hashlib
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_area

from backend import science, store
from backend.measurements import PHOTOMETRY_BAD_FLAGS, aperture
from backend.targets import TARGETS, position


def resolve_target(search, target_id):
    if target_id is None:
        return None
    target = next((t for t in TARGETS if t['id'] == target_id), None)
    if target is None:
        raise ValueError('Unknown catalogue target.')
    field = SkyCoord(search['ra'], search['dec'], unit='deg')
    preset = SkyCoord(target['field_ra'], target['field_dec'], unit='deg')
    if field.separation(preset).arcsec > 1:
        raise ValueError('The catalogue target does not match this search field.')
    return target


def spread(rows, limit):
    """Farthest-time sampling fills every slot even for clustered observations."""
    rows = sorted(rows, key=lambda r: (r['mjd'], r['id']))
    if len(rows) <= limit:
        return rows
    selected = [0]
    while len(selected) < limit:
        remaining = [i for i in range(len(rows)) if i not in selected]
        chosen = max(remaining, key=lambda i: (
            min(abs(rows[i]['mjd']-rows[j]['mjd']) for j in selected), -i))
        selected.append(chosen)
    return [rows[i] for i in sorted(selected)]


def candidate_plan(search, limit=36):
    """Balance detector coverage; reuse up to two cached epochs per detector."""
    center = SkyCoord(search['ra'], search['dec'], unit='deg')
    groups = {}
    for obs in search['observations']:
        if np.isfinite(obs['mjd']):
            groups.setdefault(obs['band'], []).append(obs)
    plans = []
    for _, rows in sorted(groups.items()):
        cached = [o for o in rows if science.download_path(o, center, search['fov_arcmin']).exists()]
        seeds = spread(cached, 2)
        # Cached seeds and a fully filled temporal sample, with no duplicated IDs.
        plan = seeds + spread(rows, max(2, int(np.ceil(limit/max(1, len(groups))))))
        seen = set()
        plans.append([o for o in plan if not (o['id'] in seen or seen.add(o['id']))])
    result = []
    for i in range(max((len(p) for p in plans), default=0)):
        for plan in plans:
            if i < len(plan) and len(result) < limit:
                result.append(plan[i])
    return result


def native_quality(path, coord, radius_arcsec):
    with fits.open(path, memmap=False) as hdus:
        image = np.asarray(hdus['IMAGE'].data, float)
        variance = np.asarray(hdus['VARIANCE'].data, float)
        flags = np.asarray(hdus['FLAGS'].data, np.uint32)
        if not u.Unit(hdus['IMAGE'].header.get('BUNIT', '')).is_equivalent(u.MJy/u.sr):
            raise ValueError('Unsupported native image unit for aperture checks.')
        spatial = WCS(hdus['IMAGE'].header)
        sx, sy = spatial.world_to_pixel(coord)
        definitions = {str(value).strip(): int(key[4:]) for key, value in hdus['FLAGS'].header.items()
                       if key.startswith('MSKN') and key[4:].isdigit()}
        badmask = sum(1 << bit for name, bit in definitions.items() if name in PHOTOMETRY_BAD_FLAGS)
        background_mask = sum(1 << bit for name, bit in definitions.items() if name == 'SOURCE')
        yy, xx = np.indices(image.shape)
        distance = spatial.pixel_to_world(xx, yy).separation(coord).arcsec
        inside = distance <= radius_arcsec
        valid = np.isfinite(image) & np.isfinite(variance) & (variance > 0) & ((flags & badmask) == 0)
        scale = np.sqrt(proj_plane_pixel_area(spatial))*3600
        margin = radius_arcsec*3/scale+1
        clipped = min(float(sx), float(sy), image.shape[1]-1-float(sx), image.shape[0]-1-float(sy)) < margin
        ix, iy = int(np.floor(float(sx)+.5)), int(np.floor(float(sy)+.5))
        central_valid = bool(0 <= ix < image.shape[1] and 0 <= iy < image.shape[0] and valid[iy, ix])
        spectral = WCS(hdus['IMAGE'].header, fobj=hdus, key='W')
        spectral.sip = None
        wl, bw = spectral.pixel_to_world(sx, sy)
        wl, bw = float(wl.to_value(u.um)), float(bw.to_value(u.um))
        spectral_valid = bool(np.isfinite([wl, bw]).all() and bw > 0)
        row = dict(wavelength_um=wl if np.isfinite(wl) else None,
                   bandwidth_um=bw if np.isfinite(bw) else None,
                   spectral_valid=spectral_valid, central_valid=central_valid,
                   local_coverage=float(np.sum(inside & valid)/max(1, inside.sum())),
                   has_image_data=bool(np.any(inside & np.isfinite(image))),
                   background_clipped=bool(clipped), aperture_valid=False,
                   neighbor_warning=False, flagged=[], source_background_pixels=0)
        if not spectral_valid:
            row['reason'] = 'Missing local spectral metadata.'
        elif clipped:
            row['reason'] = 'The background annulus extends beyond the native cutout.'
        else:
            try:
                # No flux or S/N is retained or used for choosing observations.
                measured = aperture(image, variance, flags, badmask, distance, radius_arcsec, background_mask)
                row.update(aperture_valid=True, neighbor_warning=measured['neighbor_warning'],
                           background_pixels=measured['background_pixels'],
                           source_background_pixels=measured['excluded_source_background_pixels'])
            except ValueError as exc:
                row['reason'] = str(exc)
        word = int(np.bitwise_or.reduce(flags[inside])) if inside.any() else 0
        row['flagged'] = [name for name, bit in definitions.items() if word & (1 << bit)]
        row['native_fits_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        return row


def inspect_observation(obs, search, target=None, radius_arcsec=12.4, *, offline=False):
    center = SkyCoord(search['ra'], search['dec'], unit='deg')
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        prediction = position(target, obs['mjd']) if target else dict(ra=search['ra'], dec=search['dec'], mjd=obs['mjd'])
    coord = SkyCoord(prediction['ra'], prediction['dec'], unit='deg')
    row = dict(id=obs['id'], band=obs['band'], mjd=obs['mjd'], date=obs['date'],
               prediction=prediction, cutout_fov_arcmin=search['fov_arcmin'],
               central_valid=False, aperture_valid=False, local_coverage=0., spectral_valid=False)
    try:
        path = science.download_path(obs, center, search['fov_arcmin'])
        if offline and not path.exists():
            return dict(row, reason='Native FITS is not cached; offline inspection only.')
        path = science.download(obs, center, search['fov_arcmin'], timeout=35, attempts=1)
        row.update(native_quality(path, coord, radius_arcsec))
        if row.get('background_clipped') and search['fov_arcmin'] < 30:
            expanded = min(30., max(search['fov_arcmin']*2, search['fov_arcmin']+6*radius_arcsec/60))
            larger = dict(obs, cutout_fov_arcmin=expanded)
            larger_path = science.download_path(larger, center, search['fov_arcmin'])
            if not offline or larger_path.exists():
                row['expansion_attempted_arcmin'] = expanded
                try:
                    larger_path = science.download(larger, center, search['fov_arcmin'], timeout=35, attempts=1)
                    expanded_quality = native_quality(larger_path, coord, radius_arcsec)
                    row.update(expanded_quality, cutout_fov_arcmin=expanded)
                    if row['background_clipped']:
                        row['reason'] = 'The annulus is still clipped after expansion; detector-edge coverage may be missing.'
                except Exception as exc:
                    row['expansion_error'] = f'{type(exc).__name__}: {exc}'
    except Exception as exc:
        row['reason'] = f'{type(exc).__name__}: {exc}'
    return row


def compatible(a, b):
    return (a['id'] != b['id'] and a['band'] == b['band'] and a['mjd'] != b['mjd']
            and a.get('spectral_valid') and b.get('spectral_valid')
            and abs(a['wavelength_um']-b['wavelength_um']) <= min(a['bandwidth_um'], b['bandwidth_um'])/2)


def choose(rows, limit=8):
    usable = [r for r in rows if r.get('central_valid') and r.get('spectral_valid')]
    pairs = [(a, b) for i, a in enumerate(usable) for b in usable[i+1:] if compatible(a, b)]
    if not pairs:
        # A saturated target may still be useful to view. Retain the image and
        # its warnings, while keeping every failed photometry gate unchanged.
        usable = [r for r in rows if r.get('spectral_valid') and r.get('has_image_data')]
        pairs = [(a, b) for i, a in enumerate(usable) for b in usable[i+1:] if compatible(a, b)]
    if not pairs:
        return dict(status='no_comparable_pair', selected_ids=[r['id'] for r in spread(usable, limit)],
                    pair_ids=[], summary='No locally comparable pair was found in the inspected sample. Available images can still be browsed.')

    def score(pair):
        a, b = pair
        # Preserve the aperture-quality tier, then maximise the time available
        # for visible motion. Small coverage differences must not win over it.
        return (int(a['aperture_valid'])+int(b['aperture_valid']),
                abs(a['mjd']-b['mjd']),
                -int(a.get('neighbor_warning', False))-int(b.get('neighbor_warning', False)),
                min(a['local_coverage'], b['local_coverage']))

    best = max(pairs, key=score)
    selected = list(sorted(best, key=lambda r: r['mjd']))
    # Extend only with mutually compatible epochs of at least the anchor quality.
    extra = [r for r in usable if r not in selected and (r['aperture_valid'] or not all(x['aperture_valid'] for x in best))]
    for row in sorted(extra, key=lambda r: (-int(r['aperture_valid']), r.get('neighbor_warning', False), r['mjd'])):
        if len(selected) < limit and all(compatible(row, other) for other in selected):
            selected.append(row)
    valid_pair = all(r['aperture_valid'] for r in best)
    return dict(status='aperture_pair_available' if valid_pair else 'image_pair_only',
                selected_ids=[r['id'] for r in sorted(selected, key=lambda r: r['mjd'])],
                pair_ids=[r['id'] for r in sorted(best, key=lambda r: r['mjd'])],
                baseline_days=abs(best[0]['mjd']-best[1]['mjd']),
                summary=('A pair passes the local aperture and wavelength checks; source identity and variability remain unconfirmed.' if valid_pair else
                         'A local wavelength pair is available for viewing, but its apertures do not both pass the measurement checks.'))


def selection_summary(search, target_id, candidate_limit, radius_arcsec, rows, total, complete, limit=8):
    return dict(method='target-local-selection-2', checked_at=datetime.now(timezone.utc).isoformat(),
                search_id=search['id'], target_id=target_id, radius_arcsec=radius_arcsec,
                candidate_limit=candidate_limit, inspected=len(rows), planned=total, complete=complete, candidates=rows,
                ranking='aperture-quality-then-max-baseline-1',
                position_method='catalogue_proper_motion_per_epoch' if target_id else 'fixed_ICRS_search_center',
                **choose(rows, limit), limitations=[
                    'A bounded sample across detectors, not an exhaustive search of the archive.',
                    'WCS-WAVE matching is a browsing heuristic, not a full response calibration.',
                    'Selection uses masks, background availability and dates, never target flux or S/N.',
                    'Catalogue positions include proper motion only, without parallax or source identification.',
                    'Passing aperture checks does not establish motion, variability or a detection.'])


def select_observations(search, target_id=None, candidate_limit=36, radius_arcsec=12.4, limit=8, *,
                        offline=False, progress=lambda *args: None):
    target = resolve_target(search, target_id)
    planned = candidate_plan(search, candidate_limit)
    results = {}
    progress(0, len(planned), 'Downloading observations in parallel')
    # Only this coordinator publishes state; worker threads never mutate a manifest.
    with ThreadPoolExecutor(max_workers=4, thread_name_prefix='spherex-download') as pool:
        pending = {pool.submit(inspect_observation, obs, search, target, radius_arcsec, offline=offline): obs for obs in planned}
        for future in as_completed(pending):
            obs = pending[future]
            try:
                row = future.result()
            except Exception as exc:
                row = dict(id=obs['id'], band=obs['band'], mjd=obs['mjd'], date=obs['date'],
                           aperture_valid=False, central_valid=False, local_coverage=0., spectral_valid=False,
                           reason=f'{type(exc).__name__}: {exc}')
            results[obs['id']] = row
            rows = [results[o['id']] for o in planned if o['id'] in results]
            progress(len(rows), len(planned), 'Downloading observations in parallel')
    rows = [results[o['id']] for o in planned]
    return selection_summary(search, target_id, candidate_limit, radius_arcsec, rows, len(planned), True, limit)


def build_selected_analysis(id, search, target_id=None, candidate_limit=36, radius_arcsec=12.4):
    try:
        def progress(done, total, message):
            store.put('job', id, dict(id=id, status='running', completed=done, total=total, phase='selection',
                                     message=message))
        selection = select_observations(search, target_id, candidate_limit, radius_arcsec, progress=progress)
        selection['preparation'] = 'recommended_series'
        store.put('selection', id, dict(id=id, **selection))
        if not selection['selected_ids']:
            raise ValueError('No usable local image was found in the inspected sample. Try another field, release or manual selection.')
        science.build_analysis(id, search, selection['selected_ids'], selection=selection)
    except Exception as exc:
        store.put('job', id, dict(id=id, status='failed', message=str(exc), selection_id=id))
