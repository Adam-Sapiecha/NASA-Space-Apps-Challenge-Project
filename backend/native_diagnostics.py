"""Native FITS centroid and shape diagnostics; no image enhancement or invented pixels."""
import math

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from scipy.ndimage import map_coordinates
from scipy.optimize import least_squares

from backend.calibrated import psf_at
from backend.measurements import PHOTOMETRY_BAD_FLAGS
from backend.science import download_path
from backend.coordinates import point_sky
from backend.photometry_math import epsf_profile, weighted_fit


def fit_stamp(image, variance, valid, x, y, epsf=None, oversample=(1, 1)):
    """Fit a source plus background plane within a bounded native 17x17 stamp."""
    yy, xx = np.indices(image.shape)
    good = valid & np.isfinite(image) & np.isfinite(variance) & (variance > 0)
    if good.sum() < 30 or good.mean() < .8:
        raise ValueError('Za mało ważnego pokrycia do dopasowania pozycji.')
    background = float(np.median(image[good]))
    noise = np.sqrt(variance[good])
    amplitude = max(float(np.max(image[good])-background), float(np.median(noise)))
    is_epsf = epsf is not None

    def profile(cx, cy, sigma):
        if is_epsf:
            ox, oy = oversample
            return epsf_profile(image.shape,cx,cy,epsf,ox,oy)
        return np.exp(-((xx-cx)**2+(yy-cy)**2)/(2*sigma*sigma))

    def model(p):
        amp, cx, cy, bg, gx, gy, sigma = p
        return amp*profile(cx, cy, sigma)+bg+gx*(xx-x)+gy*(yy-y)

    def residual(p):
        return (model(p)[good]-image[good])/noise

    lower = [0, max(0, x-2), max(0, y-2), -np.inf, -np.inf, -np.inf, .5]
    upper = [np.inf, min(image.shape[1]-1, x+2), min(image.shape[0]-1, y+2), np.inf, np.inf, np.inf, 3.5]
    # ePSF has fixed width; Gaussian width is fitted only for the fallback.
    initial = [amplitude, x, y, background, 0, 0, 1.2]
    if is_epsf:
        def reduced_residual(p):
            return residual(np.r_[p, 1.2])
        fit = least_squares(reduced_residual, initial[:6], bounds=(lower[:6], upper[:6]), max_nfev=200)
        params = np.r_[fit.x, 1.2]
    else:
        fit = least_squares(residual, initial, bounds=(lower, upper), max_nfev=200)
        params = fit.x
    if not fit.success or np.any(fit.active_mask):
        raise ValueError('Pozycja lub kształt osiąga granicę dopasowania; wybierz punkt bliżej źródła.')
    _, covariance, _ = weighted_fit(fit.jac, np.zeros(good.sum()), np.ones(good.sum()))
    res = residual(params)
    dof = int(good.sum()-len(fit.x))
    chi2 = float(np.dot(res, res)/dof)
    error_px = math.sqrt(max(float(covariance[1, 1]+covariance[2, 2]), 0)/2)
    snr = float(params[0]/math.sqrt(max(covariance[0, 0], 1e-30)))
    p = profile(params[1], params[2], params[6])
    signal = image-background
    positive = np.where(good, np.maximum(signal, 0), 0)
    total = positive.sum()
    moments = np.array([[np.sum(positive*(xx-params[1])**2), np.sum(positive*(xx-params[1])*(yy-params[2]))],
                        [np.sum(positive*(xx-params[1])*(yy-params[2])), np.sum(positive*(yy-params[2])**2)]])/max(total, 1e-30)
    eigen = np.maximum(np.linalg.eigvalsh(moments), 1e-8)
    return dict(x=float(params[1]), y=float(params[2]), random_error_px=error_px,
                snr=snr, reduced_chi2=chi2, elongation=float(np.sqrt(eigen[1]/eigen[0])),
                valid_fraction=float(good.mean()), negative_residual_fraction=float(np.mean(res < -3)),
                positive_residual_fraction=float(np.mean(res > 3)),
                background=float(params[3]), background_gradient=float(np.hypot(params[4], params[5])),
                profile='release_ePSF' if is_epsf else 'gaussian_fallback',
                width_px=None if is_epsf else float(params[6]), fit_pixels=int(good.sum()))


def native_profile(manifest, x, y, frame_id, systematic_floor_arcsec=2):
    frame = next((f for f in manifest['frames'] if f['id'] == frame_id), None)
    if frame is None:
        raise ValueError('Ekspozycja nie należy do analizy.')
    coord = point_sky(manifest,dict(x=x,y=y))
    search = manifest['search']
    path = download_path(frame, SkyCoord(search['ra'], search['dec'], unit='deg'), search['fov_arcmin'])
    if not path.exists():
        raise ValueError('Brak natywnego FITS w cache; przygotuj analizę ponownie.')
    with fits.open(path, memmap=False) as hdus:
        wcs = WCS(hdus['IMAGE'].header)
        sx, sy = map(float, wcs.world_to_pixel(coord))
        if not np.isfinite([sx, sy]).all():
            raise ValueError('Punkt poza obrazem.')
        ix, iy = int(round(sx)), int(round(sy))
        shape = hdus['IMAGE'].data.shape
        if min(ix, iy, shape[1]-1-ix, shape[0]-1-iy) < 8:
            raise ValueError('Źródło zbyt blisko brzegu wycinka.')
        region = np.s_[iy-8:iy+9, ix-8:ix+9]
        image = np.asarray(hdus['IMAGE'].data[region], float)
        variance = np.asarray(hdus['VARIANCE'].data[region], float)
        flags = np.asarray(hdus['FLAGS'].data[region], np.uint32)
        badmask = sum(1 << bit for name, bit in frame['flag_definitions'].items() if name in PHOTOMETRY_BAD_FLAGS)
        valid = (flags & badmask) == 0
        epsf = None
        sampling = (1, 1)
        try:
            epsf, info = psf_at(hdus, sx, sy)
            sampling = (info['oversample_x'], info['oversample_y'])
        except (KeyError, ValueError):
            pass
        fitted = fit_stamp(image, variance, valid, sx-ix+8, sy-iy+8, epsf, sampling)
        nx, ny = fitted['x']+ix-8, fitted['y']+iy-8
        fitted_coord = wcs.pixel_to_world(nx, ny)
        scale = float(np.sqrt(abs(np.linalg.det(wcs.pixel_scale_matrix)))*3600)
        random_error = fitted['random_error_px']*scale
        fitted.update(frame_id=frame_id, mjd=frame['mjd'], date=frame['date'],
                      ra=float(fitted_coord.ra.deg), dec=float(fitted_coord.dec.deg),
                      random_error_arcsec=random_error, systematic_floor_arcsec=systematic_floor_arcsec,
                      error_arcsec=math.hypot(random_error, systematic_floor_arcsec),
                      centroid_shift_arcsec=float(coord.separation(fitted_coord).arcsec),
                      bad_fraction=float(np.mean(~valid)), source_sha256=frame['sha256'],
                      selected_point=dict(x=x, y=y), obs_id=frame.get('obs_id'),collection=frame.get('collection',search.get('collection')),
                      method='native-centroid-2')
        return fitted


def profile_series(manifest, x, y, progress=lambda i, n: None):
    rows = []
    for i, frame in enumerate(manifest['frames']):
        progress(i, len(manifest['frames']))
        try:
            row = dict(valid=True, **native_profile(manifest, x, y, frame['id']))
        except (ValueError, KeyError, OSError) as exc:
            row = dict(frame_id=frame['id'], valid=False, reason=str(exc))
        rows.append(row)
    return dict(kind='profile', analysis_id=manifest['id'], point=dict(x=x, y=y), rows=rows,
                method='native-profile-series-2', limitations=[
                    'Dopasowanie izolowanego źródła; bez wspólnego modelowania sąsiadów.',
                    'Próg i podłoga astrometrii 2″ są ustawieniami eksploracyjnymi, nie kalibracją instrumentu.',
                    'Gauss zastępuje brakujący ePSF tylko do diagnostyki; nie poświadcza poprawnej fotometrii.',
                    'Pozycje startowe są stałe. Dla źródła ruchomego dodawaj pomiary w jego pozycji dla każdej epoki.'])
