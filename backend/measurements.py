"""Exploratory aperture measurements on native pixels, before interpolation.

Random errors assume independent native pixels. No total-flux/PSF calibration,
correlated-noise significance, automatic source identification or discovery claims.
"""
import hashlib
import json
import httpx

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_area

from backend import store
from backend.science import BAD_FLAGS, download_path
from backend.coordinates import point_sky
from backend.irsa_resources import calibration_product, calibration_cutout

PHOTOMETRY_BAD_FLAGS = BAD_FLAGS | {'PHANMISS', 'PERSIST', 'OUTLIER', 'CROSSTALK',
                                  'GHOST', 'GHOST_FPA', 'GHOST_EXT', 'STREAK', 'BLOOM', 'SNOWBALL', 'HALO',
                                  'SATELLITE_HALO', 'DICHROIC'}


def aperture(data, variance, flags, badmask, distance, radius, background_mask=0, pixel_factor=None):
    source = distance <= radius
    annulus = (distance >= radius*1.8) & (distance <= radius*3)
    valid = np.isfinite(data) & np.isfinite(variance) & (variance > 0) & ((flags & badmask) == 0)
    n = int(source.sum())
    if n < 3 or np.sum(source & valid) != n or np.sum(annulus & valid) < 12:
        raise ValueError("Niepełna apertura, flagi, brak wariancji lub za mało pikseli tła.")
    # A known source is usable in the target aperture, but contaminates the sky.
    bg = annulus & valid & ((flags & background_mask) == 0)
    if np.sum(bg) < 12:
        raise ValueError('Za mało pikseli tła po wykluczeniu znanych źródeł.')
    # Fixed mean estimator permits an explicit linear variance propagation.
    background = float(np.mean(data[bg]))
    flux = float(np.sum(data[source])-n*background)
    var = float(np.sum(variance[source])+n*n*np.sum(variance[bg])/np.sum(bg)**2)
    scatter = float(np.std(data[bg]))
    # Diagnostic only: no claim that this proves isolation.
    contaminated = bool(np.any(data[bg]-background > 5*np.sqrt(variance[bg])))
    result = dict(aperture_sum=flux, random_error=float(np.sqrt(var)), background=background,
                background_scatter=scatter, aperture_pixels=n, background_pixels=int(bg.sum()),
                neighbor_warning=contaminated, excluded_source_background_pixels=int(np.sum(annulus & ((flags & background_mask) != 0))),
                flags_word=int(np.bitwise_or.reduce(flags[source])))
    if pixel_factor is not None:
        k = np.broadcast_to(pixel_factor, data.shape)
        if not np.isfinite(k[source | bg]).all() or np.any(k[source | bg] <= 0):
            raise ValueError('Brak poprawnej powierzchni pikseli apertury lub tła.')
        total = k[source].sum()
        result.update(flux_mjy=float(np.sum(k[source]*(data[source]-background))),
                      error_mjy=float(np.sqrt(np.sum(k[source]**2*variance[source])+total**2*np.sum(variance[bg])/bg.sum()**2)))
    return result


def measure(manifest, x, y, radius_arcsec):
    key = hashlib.sha256(json.dumps([manifest['id'], x, y, radius_arcsec, 'native-aperture-area-3']).encode()).hexdigest()
    cached = store.get('measurement', key)
    if cached:
        # Legacy records predate the point field. The cache key already binds
        # this exact x/y and radius, so metadata can be restored without a new fit.
        if 'point' not in cached:
            cached['point'] = dict(x=x, y=y)
            store.put('measurement', key, cached)
        return cached
    coord = point_sky(manifest, dict(x=x, y=y))
    rows = []
    for frame in manifest['frames']:
        row = dict(id=frame['id'], date=frame['date'], mjd=frame['mjd'], band=frame['band'])
        try:
            search = manifest['search']
            center = SkyCoord(search['ra'], search['dec'], unit='deg')
            path = download_path(frame, center, search['fov_arcmin'])
            if not path.exists():
                raise ValueError("Brak źródłowego FITS w cache; przygotuj analizę ponownie.")
            with fits.open(path, memmap=False) as hdus:
                data = hdus['IMAGE'].data.astype(float)
                variance = hdus['VARIANCE'].data.astype(float)
                flags = hdus['FLAGS'].data.astype(np.uint32)
                spatial = WCS(hdus['IMAGE'].header)
                yy, xx = np.indices(data.shape)
                distance = spatial.pixel_to_world(xx, yy).separation(coord).arcsec
                # Reject apertures truncated at the product boundary.
                sx, sy = spatial.world_to_pixel(coord)
                scale = np.sqrt(proj_plane_pixel_area(spatial))*3600
                margin = radius_arcsec*3/scale+1
                if min(sx, sy, data.shape[1]-1-sx, data.shape[0]-1-sy) < margin:
                    raise ValueError("Pierścień tła wykracza poza wycinek FITS.")
                mask = sum(1 << bit for name, bit in frame['flag_definitions'].items() if name in PHOTOMETRY_BAD_FLAGS)
                background_mask = sum(1 << bit for name, bit in frame['flag_definitions'].items() if name == 'SOURCE')
                if not u.Unit(hdus['IMAGE'].header['BUNIT']).is_equivalent(u.MJy/u.sr):
                    raise ValueError("Nieobsługiwana jednostka fotometrii.")
                area_path, area_provenance = calibration_product(search['collection'], 'solid_angle_pixel_map', int(hdus['IMAGE'].header['DETECTOR']))
                solid_angle = calibration_cutout(area_path, 'IMAGE', hdus['IMAGE'].header, data.shape)
                factor = (u.Unit(hdus['IMAGE'].header['BUNIT'])*u.arcsec**2).to(u.mJy)*solid_angle
                values = aperture(data, variance, flags, mask, distance, radius_arcsec, background_mask, factor)
                spectral = WCS(hdus['IMAGE'].header, fobj=hdus, key='W')
                spectral.sip = None
                wl, bw = spectral.pixel_to_world(sx, sy)
                if not np.isfinite(wl.to_value(u.um)) or not np.isfinite(bw.to_value(u.um)):
                    raise ValueError("Brak lokalnej długości fali.")
                row.update(values, valid=True, wavelength_um=float(wl.to_value(u.um)),
                           bandwidth_um=float(bw.to_value(u.um)), unit='mJy',
                           calibration_sources=[area_provenance], position=dict(ra=float(coord.ra.deg), dec=float(coord.dec.deg)),
                           flagged=[name for name, bit in frame['flag_definitions'].items() if values['flags_word'] & (1 << bit)])
        except (ValueError, KeyError, OSError, httpx.HTTPError) as exc:
            row.update(valid=False, reason=str(exc))
        rows.append(row)
    result = dict(id=key, analysis_id=manifest['id'], point=dict(x=x, y=y), ra=float(coord.ra.deg), dec=float(coord.dec.deg),
                  radius_arcsec=radius_arcsec, rows=rows, method='native-aperture-area-3',
                  limitations=['Pomiar eksploracyjny apertury, bez korekty PSF/apertury; nie jest całkowitym strumieniem źródła.',
                               'Błąd losowy z VARIANCE i średniego tła przy założeniu niezależnych pikseli; bez błędów systematycznych i korelacji.',
                               'Pozycja pola stała w ICRS; dla ruchomego źródła wybierz pozycję osobno w każdej ekspozycji.',
                               'Pierścień tła 1,8–3 promieni, bez pikseli SOURCE. Ostrzeżenie sąsiada nie potwierdza izolacji.',
                               'Długość fali z WCS-WAVE jest przybliżeniem do podglądu; brak kalibracyjnych CWAVE/CBAND.'])
    store.put('measurement', key, result)
    return result


def recommend(measurement):
    rows = [r for r in measurement['rows'] if r['valid'] and not r['neighbor_warning'] and not r['flagged']]
    # Publish diagnostic availability, never optimize apparent SNR on the target.
    return dict(status='insufficient_validation', weights=None,
                reason='Brak zwalidowanej korekty apertury/PSF i niezależnej próby kontrolnej. Brak wiarygodnej rekomendacji.',
                criterion='Dostępność pomiarów bez flag i ostrzeżenia sąsiada; nie ranking prawdopodobieństwa odkrycia.',
                usable_measurements=len(rows), availability=[dict(id=r['id'], date=r['date'],
                wavelength_um=r['wavelength_um'], bandwidth_um=r['bandwidth_um'], error_mjy=r['error_mjy']) for r in rows])
