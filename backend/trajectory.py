"""Catalog propagation, JPL ephemerides and bounded tangent-plane linear motion."""
import warnings

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from astroquery.jplhorizons import Horizons
from backend.photometry_math import weighted_fit


def linear_motion(observations, prediction_mjds):
    if len(observations) < 3 or len({r['mjd'] for r in observations}) < 3:
        raise ValueError('Potrzebne co najmniej trzy zmierzone pozycje w różnych terminach.')
    values = np.array([[r['ra'], r['dec'], r['mjd'], r['error_arcsec']] for r in observations], float)
    if not np.isfinite(values).all() or np.any(values[:, 3] <= 0):
        raise ValueError('Pozycje i dodatnie niepewności muszą być skończone.')
    coords = SkyCoord(values[:, 0], values[:, 1], unit='deg')
    origin = coords[0]
    east, north = origin.spherical_offsets_to(coords)
    positions = np.column_stack((east.arcsec, north.arcsec))
    if np.max(np.linalg.norm(positions, axis=1)) > 1800:
        raise ValueError('Liniowy model lokalny obsługuje trasę do 30 minut łuku.')
    epoch = float(np.mean(values[:, 2]))
    times = values[:, 2]-epoch
    baseline = float(np.ptp(times))
    design = np.column_stack((np.ones(len(times)), times))
    weighted = design/values[:, 3, None]
    fitted = [weighted_fit(design, positions[:,axis], values[:,3]) for axis in range(2)]
    beta = np.column_stack([f[0] for f in fitted])
    covariance, condition = fitted[0][1], fitted[0][2]
    residual = positions-design@beta
    chi2 = float(np.sum((residual/values[:, 3, None])**2)/(2*len(times)-4))
    # Formal covariance inflated for observed scatter, never shrunk below input errors.
    covariance *= max(1, chi2)
    predictions = []
    for mjd in prediction_mjds:
        if not np.isfinite(mjd) or mjd < values[:, 2].min()-baseline or mjd > values[:, 2].max()+min(baseline, 365):
            raise ValueError('Prognoza może wykraczać najwyżej o jedną bazę czasową, do 365 dni w przyszłość.')
        vector = np.array([1, mjd-epoch])
        offset = vector@beta
        coord = origin.spherical_offsets_by(offset[0]*u.arcsec, offset[1]*u.arcsec)
        predictions.append(dict(mjd=float(mjd), ra=float(coord.ra.deg), dec=float(coord.dec.deg),
                                axis_error_arcsec=float(np.sqrt(vector@covariance@vector))))
    held_out = []
    if len(observations) >= 4:
        for i in range(len(times)):
            keep = np.arange(len(times)) != i
            if len(np.unique(times[keep])) < 2:
                continue
            fitted = np.linalg.lstsq(weighted[keep], (positions/values[:, 3, None])[keep], rcond=None)[0]
            held_out.append(float(np.linalg.norm(positions[i]-design[i]@fitted)))
    return dict(kind='motion', method='weighted-tangent-linear-1', status='exploratory',
                reference_mjd=epoch, baseline_days=baseline, observations=observations,
                motion_east_arcsec_day=float(beta[1, 0]), motion_north_arcsec_day=float(beta[1, 1]),
                reduced_chi2=chi2, fit_warning=chi2 > 3, condition_number=condition,
                residual_rms_arcsec=float(np.sqrt(np.mean(np.sum(residual**2, axis=1)))),
                held_out_errors_arcsec=held_out, predictions=predictions,
                limitations=['Lokalny ruch liniowy na sferze, nie orbita ani model paralaksy.',
                             'Niepewność osi pochodzi z błędów pozycji i rozrzutu; nie uwzględnia błędu modelu ruchu.',
                             'Przy dużych resztach lub krótkiej bazie prognoza jest niewiarygodna.',
                             'Pozycje muszą dotyczyć tego samego źródła. Nie łączymy detekcji automatycznie.'])


def star_positions(candidate, mjds):
    needed = ('reference_ra', 'reference_dec', 'pmra', 'pmdec', 'reference_epoch')
    if any(candidate.get(k) is None for k in needed):
        raise ValueError('Brak ruchu własnego lub pozycji odniesienia. Pobierz nowy katalog Gaia.')
    coord = SkyCoord(candidate['reference_ra']*u.deg, candidate['reference_dec']*u.deg,
                     pm_ra_cosdec=candidate['pmra']*u.mas/u.yr, pm_dec=candidate['pmdec']*u.mas/u.yr,
                     obstime=Time(candidate['reference_epoch'], format='jyear'))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        result = coord.apply_space_motion(new_obstime=Time(mjds, format='mjd'))
    return dict(kind='star_motion', method='gaia-proper-motion-1', candidate_id=candidate['id'],
                predictions=[dict(mjd=float(m), ra=float(c.ra.deg), dec=float(c.dec.deg), axis_error_arcsec=None)
                             for m, c in zip(mjds, result)], limitations=[
                    'Prosta propagacja ruchu własnego z Gaia, bez paralaksy, prędkości radialnej i pozycji pozornej.',
                    'Brak propagowanej kowariancji astrometrii; nie podajemy wymyślonej dokładności.',
                    'Prognoza dotyczy wybranego wpisu Gaia, nie potwierdza jego identyfikacji na zdjęciu.'])


def ephemeris(name, mjds, observer='500@399'):
    obj = Horizons(id=name, location=observer, epochs=[float(m)+2400000.5 for m in mjds])
    obj.TIMEOUT = 30
    table = obj.ephemerides(quantities='1,36', extra_precision=True)
    predictions = []
    for row in table:
        def optional(key):
            if key not in table.colnames or np.ma.is_masked(row[key]): return None
            value = float(row[key])
            return value if np.isfinite(value) else None
        predictions.append(dict(mjd=float(row['datetime_jd'])-2400000.5,
                                ra=float(row['RA']), dec=float(row['DEC']),
                                ra_3sigma_arcsec=optional('RA_3sigma'), dec_3sigma_arcsec=optional('DEC_3sigma')))
    return dict(kind='ephemeris', method='JPL-Horizons', object=name,
                resolved_name=str(table['targetname'][0]) if len(table) else name,
                observer=observer, predictions=predictions,
                source='https://ssd.jpl.nasa.gov/horizons/', limitations=[
                    'Efemeryda znanego obiektu, nie orbita dopasowana do wskazań użytkownika.',
                    'Obserwator 500@399 oznacza środek Ziemi. Inny punkt obserwacji zmienia pozycję.',
                    'Efemerydy ziemskie nie są pozycjami widzianymi ze SPHEREx.',
                    'Niepewności 3σ zwracamy tylko wtedy, gdy podaje je Horizons.'])
