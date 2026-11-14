"""Reproducible point-level assessment. No trained classifier or discovery score."""
import hashlib
import json
import math
from datetime import datetime, timezone

from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

from backend import catalogs, store
from backend.measurements import measure, PHOTOMETRY_BAD_FLAGS
from backend.coordinates import point_sky

VERSION = 'source-assessment-1'


def source_record(manifest, x, y):
    identity = [manifest['id'], x, y, VERSION]
    key = hashlib.sha256(json.dumps(identity).encode()).hexdigest()
    existing = store.get('source', key)
    if existing:
        return existing
    coord = point_sky(manifest,dict(x=x,y=y))
    result = dict(id=key, analysis_id=manifest['id'], point=dict(x=x, y=y),
                  ra=float(coord.ra.deg), dec=float(coord.dec.deg), coordinate_frame='ICRS',
                  position_method='user_selected_point', position_error_arcsec=None,
                  method=VERSION, created_at=datetime.now(timezone.utc).isoformat())
    store.put('source', key, result)
    return result


def rank_matches(ra, dec, catalog, radius_arcsec):
    """Angular candidates only: never equate proximity with identification."""
    target = SkyCoord(ra, dec, unit='deg')
    candidates = []
    for row in catalog['sources']:
        separation = float(target.separation(SkyCoord(row['ra'], row['dec'], unit='deg')).arcsec)
        if separation <= radius_arcsec:
            candidates.append(dict(**row, separation_arcsec=separation,
                                   name=f"Gaia DR3 {row['id']}", object_type=None))
    candidates.sort(key=lambda row: row['separation_arcsec'])
    return candidates


def identify(manifest, x, y, frame_id, radius_arcsec):
    frame = next((f for f in manifest['frames'] if f['id'] == frame_id), None)
    if frame is None:
        raise ValueError('Wybierz ekspozycję tej analizy.')
    source = source_record(manifest, x, y)
    # A larger catalog cone allows some proper-motion ingress; not exhaustive.
    catalog = catalogs.gaia(source['ra'], source['dec'], max(2, radius_arcsec/60), frame['mjd'])
    candidates = rank_matches(source['ra'], source['dec'], catalog, radius_arcsec)
    result = dict(source=source, frame_id=frame_id, mjd=frame['mjd'],
                  radius_arcsec=radius_arcsec, catalog_id=catalog['id'],
                  catalog='Gaia DR3', candidates=candidates,
                  status='candidates' if candidates else 'no_match',
                  method='angular-candidates-1', truncated=catalog['truncated'],
                  limitations=[
                      'Pozycja pochodzi z kliknięcia, bez dopasowania środka i niepewności astrometrii.',
                      'Bliskość nie potwierdza identyfikacji; sygnał może zawierać kilka źródeł.',
                      'Gaia nie dostarcza tutaj typu obiektu. Brak dopasowania nie oznacza odkrycia.',
                      'Ruch własny propagowano tylko tam, gdzie jest dostępny; bez paralaksy i pozycji pozornej.',
                      'Stożek katalogowy i limit wyników mogą pominąć odpowiedniki, w tym szybko poruszające się źródła.'])
    key = hashlib.sha256(json.dumps([source['id'], frame_id, catalog['id'], radius_arcsec, result['method']]).encode()).hexdigest()
    result['id'] = key
    store.put('identification', key, result)
    return result


def assess_row(row):
    warnings = []
    if not row.get('valid'):
        return dict(frame_id=row['id'], status='unusable', warnings=[row.get('reason') or 'Brak ważnego pomiaru.'], snr=None)
    flux, error = row.get('flux_mjy'), row.get('error_mjy')
    numeric = all(isinstance(v, (int, float)) and math.isfinite(v) for v in (flux, error)) and error > 0
    if not numeric:
        return dict(frame_id=row['id'], status='unusable', warnings=['Niepoprawny strumień lub błąd pomiaru.'], snr=None)
    flags = row.get('flagged', [])
    bad = sorted(set(flags) & PHOTOMETRY_BAD_FLAGS)
    if bad:
        warnings.append('Flagi problemów: '+', '.join(bad))
    other = sorted(set(flags) - PHOTOMETRY_BAD_FLAGS)
    if other:
        warnings.append('Pozostałe flagi do przeglądu: '+', '.join(other))
    if row.get('neighbor_warning'):
        warnings.append('Możliwe zanieczyszczenie pierścienia tła.')
    snr = flux/error
    if snr < 5:
        warnings.append('Słaby lub ujemny sygnał apertury; to nie dowód artefaktu.')
    return dict(frame_id=row['id'], status='review' if warnings else 'no_rule_warning',
                snr=snr, warnings=warnings)


def quality_report(manifest, x, y, radius_arcsec):
    source = source_record(manifest, x, y)
    measurement = measure(manifest, x, y, radius_arcsec)
    key = hashlib.sha256((measurement['id']+VERSION).encode()).hexdigest()
    result = dict(id=key, source_id=source['id'], analysis_id=manifest['id'],
                  point=source['point'], radius_arcsec=radius_arcsec,
                  measurement_id=measurement['id'], method='aperture-quality-rules-1',
                  model=None, rows=[assess_row(r) for r in measurement['rows']],
                  inputs=[dict(frame_id=f['id'], sha256=f.get('sha256')) for f in manifest['frames']],
                  limitations=['Reguły jakości apertury, nie klasyfikator artefaktów.',
                               'Brak ostrzeżeń nie potwierdza rzeczywistego źródła ani poprawnego PSF.',
                               'SNR obejmuje formalny błąd losowy; bez pełnej systematyki.',
                               'Oceny użytkownika są etykietami do weryfikacji, nie prawdą referencyjną.'])
    store.put('quality_report', key, result)
    return result


def weighted_flux(report, frame_ids, max_hours):
    """Explicit exploratory average; never changes image weights or selects bands."""
    from backend.calibrated import require_current_report
    require_current_report(report)
    if len(frame_ids) < 2 or len(set(frame_ids)) != len(frame_ids):
        raise ValueError('Wybierz różne ekspozycje.')
    lookup = {r['id']: r for r in report['rows']}
    if not set(frame_ids) <= lookup.keys():
        raise ValueError('Ekspozycja nie należy do raportu kalibracji.')
    rows = [lookup[k] for k in frame_ids]
    hashes = [r['source_sha256'] for r in rows if r.get('source_sha256')]
    if len(set(hashes)) != len(hashes):
        raise ValueError('Powtórzony źródłowy FITS nie jest niezależnym pomiarem.')
    for row in rows:
        fit = row.get('epsf', {})
        values = [fit.get('flux_mjy'), fit.get('error_mjy'), row.get('wavelength_um'), row.get('bandwidth_um'), row.get('mjd')]
        if not row.get('valid') or not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values) or values[1] <= 0 or values[3] <= 0:
            raise ValueError('Wymagane ważne pomiary ePSF z dodatnimi błędami i szerokością pasma.')
    if (max(r['mjd'] for r in rows)-min(r['mjd'] for r in rows))*24 > max_hours:
        raise ValueError('Przekroczono wybrane okno czasu.')
    for a in rows:
        for b in rows:
            if abs(a['wavelength_um']-b['wavelength_um']) > min(a['bandwidth_um'], b['bandwidth_um'])/2:
                raise ValueError('Niezgodne lokalne pasma; brak wspólnej wielkości do uśrednienia.')
    # Relative scaling avoids overflow for very small positive errors.
    scale = min(r['epsf']['error_mjy'] for r in rows)
    weights = [(scale/r['epsf']['error_mjy'])**2 for r in rows]
    total = sum(weights)
    weights = [w/total for w in weights]
    return dict(method='inverse-random-variance-epsf-1', status='exploratory',
                frame_ids=frame_ids, weights=weights,
                flux_mjy=sum(w*r['epsf']['flux_mjy'] for w, r in zip(weights, rows)),
                random_error_mjy=scale/math.sqrt(total), max_hours=max_hours,
                limitations=['Zakłada stały strumień i niezależne błędy losowe; bez wspólnej systematyki kalibracji.',
                             'Zgodność pasm jest heurystyką, nie równoważnością odpowiedzi filtrów.',
                             'Lokalna metoda ePSF wymaga walidacji względem IRSA; sprawdź flagi i sąsiadów.',
                             'To średnia pomiarów w stałym punkcie; nie śledzi ruchu i nie zmienia wag obrazów.'])
