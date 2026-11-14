"""Exploratory F_nu continuum fitting and conservative absorption-window checks."""
import numpy as np
from backend.photometry_math import weighted_fit

FEATURES = [
    dict(name='H₂O — lód', center_um=3.05, core=(2.95, 3.15), left=(2.65, 2.85), right=(3.3, 3.55)),
    dict(name='CO₂', center_um=4.27, core=(4.23, 4.31), left=(4.05, 4.18), right=(4.35, 4.48)),
    dict(name='CO', center_um=4.67, core=(4.62, 4.72), left=(4.49, 4.60), right=(4.77, 4.95)),
]
FEATURE_SOURCE = 'https://irsa.ipac.caltech.edu/onlinehelp/spherex/help.pdf'


def band_samples(rows):
    # Explicit top-hat approximation. Actual response curves are not fabricated.
    return np.array([np.linspace(r['wavelength_um']-r['bandwidth_um']/2,
                                  r['wavelength_um']+r['bandwidth_um']/2, 31) for r in rows])


def average_band(values, waves):
    return np.trapezoid(values, waves, axis=1)/(waves[:, -1]-waves[:, 0])


def planck_fnu(wavelength_um, temperature):
    frequency = 299792458/(wavelength_um*1e-6)
    exponent = np.clip(6.62607015e-34*frequency/(1.380649e-23*temperature), 1e-8, 700)
    result = (frequency/1e14)**3/np.expm1(exponent)
    return result/max(float(np.max(result)), 1e-100)


def fit_scale(shape, flux, error):
    weighted = shape/error
    denominator = float(np.dot(weighted, weighted))
    if denominator <= 0 or not np.isfinite(denominator):
        raise ValueError('Wzorzec nie wnosi sygnału w wybranych pasmach.')
    amplitude = max(0., float(np.dot(weighted, flux/error)/denominator))
    predicted = shape*amplitude
    return dict(amplitude_mjy=amplitude, chi2=float(np.sum(((flux-predicted)/error)**2)),
                predicted_mjy=predicted.tolist())


def absorption_check(rows, feature):
    x = np.array([r['wavelength_um'] for r in rows])
    width = np.array([r['bandwidth_um'] for r in rows])
    def covered(window):
        return (x-width/2 >= window[0]) & (x+width/2 <= window[1])
    core, left, right = (covered(feature[k]) for k in ('core', 'left', 'right'))
    counts = dict(core=int(core.sum()), left=int(left.sum()), right=int(right.sum()))
    result = dict(name=feature['name'], center_um=feature['center_um'], coverage=counts,
                  source=FEATURE_SOURCE, status='insufficient_coverage', depth=None,
                  contrast_mjy=None, random_error_mjy=None, formal_ratio=None)
    if counts['core'] < 1 or counts['left'] < 2 or counts['right'] < 2:
        return result
    continuum = left | right
    flux = np.array([r['flux'] for r in rows])
    error = np.array([r['error'] for r in rows])
    design = np.column_stack((np.ones(len(x)), x-feature['center_um']))
    beta,covariance,_ = weighted_fit(design[continuum],flux[continuum],error[continuum])
    weights = 1/error[core]**2
    weights /= weights.sum()
    vector = weights@design[core]
    expected = float(vector@beta)
    observed = float(weights@flux[core])
    contrast = expected-observed
    sigma = float(np.sqrt(vector@covariance@vector+np.sum((weights*error[core])**2)))
    result.update(status='depression_candidate' if contrast > 3*sigma else 'no_clear_depression',
                  depth=contrast/expected if expected > 0 else None,
                  contrast_mjy=contrast, random_error_mjy=sigma, formal_ratio=contrast/sigma)
    if expected <= 0:
        result.update(status='invalid_continuum', depth=None)
    return result


def interpret(report, frame_ids, max_hours=24, templates=None):
    from backend.calibrated import require_current_report
    require_current_report(report)
    if len(frame_ids) < 4 or len(set(frame_ids)) != len(frame_ids):
        raise ValueError('Wybierz co najmniej cztery różne pomiary.')
    lookup = {r['id']: r for r in report['rows']}
    if not set(frame_ids) <= lookup.keys():
        raise ValueError('Pomiar nie należy do raportu.')
    rows = []
    for frame_id in frame_ids:
        row = lookup[frame_id]
        fit = row.get('epsf', {})
        values = [fit.get('flux_mjy'), fit.get('error_mjy'), row.get('wavelength_um'), row.get('bandwidth_um'), row.get('mjd')]
        if not row.get('valid') or not all(isinstance(v, (int, float)) and np.isfinite(v) for v in values) or values[1] <= 0 or values[3] <= 0 or values[2] <= values[3]/2:
            raise ValueError('Wybrane pomiary muszą mieć ważny ePSF, lokalne pasma i błędy.')
        rows.append(dict(id=frame_id, flux=values[0], error=values[1], wavelength_um=values[2], bandwidth_um=values[3], mjd=values[4]))
    if len({round(r['wavelength_um'], 4) for r in rows}) < 4:
        raise ValueError('Za mało różnych długości fal.')
    if (max(r['mjd'] for r in rows)-min(r['mjd'] for r in rows))*24 > max_hours:
        raise ValueError('Przekroczono okno widma. Różne terminy mogą imitować cechy widmowe.')
    wave = band_samples(rows)
    flux = np.array([r['flux'] for r in rows])
    error = np.array([r['error'] for r in rows])
    candidates = []
    for temperature in (300, 500, 700, 1000, 1500, 2000, 2500, 3000, 4000, 5000, 6500, 8000, 12000):
        shape = average_band(planck_fnu(wave, temperature), wave)
        candidates.append(dict(name=f'Kontinuum Plancka {temperature} K', family='blackbody', temperature_k=temperature,
                               **fit_scale(shape, flux, error)))
    for slope in (-3, -2, -1, 0, 1, 2, 3):
        candidates.append(dict(name=f'Kontinuum Fν ∝ λ^{slope}', family='power_law',
                               **fit_scale(average_band((wave/2.)**slope, wave), flux, error)))
    imported = []
    for template in templates or []:
        tx = np.array(template['wavelength_um'], float)
        ty = np.array(template['relative_fnu'], float)
        if len(tx) < 4 or len(tx) != len(ty) or not np.isfinite(tx).all() or not np.isfinite(ty).all() or np.any(np.diff(tx) <= 0) or np.any(ty < 0) or not np.any(ty > 0):
            raise ValueError('Wzorzec wymaga rosnących fal i skończonych, nieujemnych Fν.')
        if tx[0] > wave.min() or tx[-1] < wave.max():
            raise ValueError('Wzorzec nie pokrywa całego zakresu odpowiedzi wybranych pasm.')
        shape = average_band(np.interp(wave, tx, ty), wave)
        fit = dict(name=template['name'], family='user_template', provenance=template['provenance'], **fit_scale(shape, flux, error))
        candidates.append(fit)
        imported.append(template)
    candidates.sort(key=lambda c: c['chi2'])
    for candidate in candidates:
        candidate['reduced_chi2'] = candidate['chi2']/(len(rows)-1)
    return dict(kind='spectrum_model', method='band-averaged-fnu-1', calibrated_result_id=report['id'],
                analysis_id=report['analysis_id'], point=report['point'], frame_ids=frame_ids,
                max_hours=max_hours, rows=rows, models=candidates[:6], imported_templates=imported,
                features=[absorption_check(rows, feature) for feature in FEATURES],
                limitations=['Pasma przybliżono prostokątem z CWAVE/CBAND, bez pełnych krzywych transmisji.',
                             'Temperatura Plancka opisuje dopasowanie kontinuum; nie jest pomiarem temperatury gwiazdy.',
                             'Zagłębienie w oknie jest kandydatem cechy, nie potwierdzeniem związku chemicznego.',
                             'Kontinuum, pył, zmienność, sąsiedzi i błędy kalibracji mogą dawać podobne wyniki.',
                             'Formalny stosunek kontrastu do błędu nie uwzględnia systematyki ani wielokrotnego testowania.',
                             'Nie wyznaczamy składu procentowego. Wzorce użytkownika nie są automatycznie zweryfikowane.'])
