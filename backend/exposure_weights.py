"""Source-local, explicitly experimental exposure weighting from native fits."""
import numpy as np


def weight_plan(report, profiles, anchor_id, max_hours):
    from backend.calibrated import require_current_report
    require_current_report(report)
    rows = {r['id']: r for r in report['rows']}
    if anchor_id not in rows or not rows[anchor_id].get('valid'):
        raise ValueError('Wybierz ważny pomiar odniesienia ePSF.')
    anchor = rows[anchor_id]
    shape = {r['frame_id']: r for r in profiles['rows']}
    selected, excluded = [], []
    ordered = sorted(rows.values(), key=lambda r: (r['id'] != anchor_id, abs(r.get('mjd', anchor['mjd'])-anchor['mjd']), r['id']))
    for row in ordered:
        profile = shape.get(row['id'], {})
        reason = None
        fit = row.get('epsf', {})
        if not row.get('valid') or not profile.get('valid'):
            reason = 'Brak ważnego pomiaru lub diagnostyki natywnego obrazu.'
        elif not np.isfinite(fit.get('error_mjy', np.nan)) or fit['error_mjy'] <= 0:
            reason = 'Niepoprawna wariancja.'
        elif row.get('neighbor_warning'):
            reason = 'Ostrzeżenie sąsiada w tle.'
        elif profile['reduced_chi2'] > 3 or profile['bad_fraction'] > .05:
            reason = 'Słaba zgodność PSF lub wadliwe pokrycie.'
        elif any(abs(row['wavelength_um']-r['wavelength_um']) > min(row['bandwidth_um'], r['bandwidth_um'])/2 for r in selected):
            reason = 'Niezgodne lokalne pasma.'
        elif any(abs(row['mjd']-r['mjd'])*24 > max_hours for r in selected):
            reason = 'Przekroczone wspólne okno czasu.'
        elif any(row.get('source_sha256') and row['source_sha256'] == r.get('source_sha256') for r in selected):
            reason = 'Powtórzony źródłowy FITS.'
        if reason:
            excluded.append(dict(frame_id=row['id'], reason=reason))
        else:
            selected.append(row)
    if not selected or selected[0]['id'] != anchor_id:
        return dict(kind='weight_plan', status='unavailable', frame_ids=[], weights=[], excluded=excluded,
                    reason='Pomiar odniesienia nie spełnia warunków jakości.')
    errors = np.array([r['epsf']['error_mjy'] for r in selected])
    relative = (errors.min()/errors)**2
    relative /= relative.sum()
    return dict(kind='weight_plan', status='exploratory' if len(selected) >= 2 else 'insufficient_comparable_frames',
                frame_ids=[r['id'] for r in selected], weights=relative.tolist(), excluded=excluded,
                anchor_id=anchor_id, max_hours=max_hours, method='native-quality-inverse-variance-1',
                calibrated_result_id=report['id'], profile_result_id=profiles['id'],
                point=report['point'], analysis_id=report['analysis_id'],
                limitations=['Dobór lokalny dla jednego źródła, nie optymalizacja całego pola.',
                             'Progi jakości są eksploracyjne; brak badania poprawy wykrywalności.',
                             'Stałe wagi wynikają z błędów ePSF po filtracji jakości natywnych FITS, bez ML.',
                             'Zgodność lokalnych pasm jest heurystyką, bez pełnej odpowiedzi filtrów.',
                             'Składanie obrazów pozostaje jakościowe, bez dopasowania PSF i propagacji kowariancji.',
                             'Dla ruchu i zmienności ogranicz okno czasu. Nie dobieraj innych wag po cichu dla każdej epoki.'])
