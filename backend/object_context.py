"""Bounded catalog adapters. Catalog associations remain candidate associations."""
import hashlib
import io
import json
from datetime import datetime, timezone

import httpx
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io.votable import parse_single_table
from astropy.time import Time
from astropy.wcs import WCS
from astropy.table import Table

from backend import catalogs, store
from backend.source_assessment import source_record

SERVICES = {'simbad': 'https://simbad.cds.unistra.fr/simbad/sim-tap/sync',
            'allwise': 'https://irsa.ipac.caltech.edu/TAP/sync'}
SIMBAD_MIRROR = 'https://simbad.harvard.edu/simbad/sim-tap/sync'


class CatalogRows(list):
    """Rows with transport provenance, still compatible with ordinary test lists."""
    def __init__(self, source_url, response):
        super().__init__()
        self.source_url = source_url
        self.response_sha256 = hashlib.sha256(response).hexdigest()


def tap(service, query):
    table = None
    error = None
    urls = [SERVICES[service], SIMBAD_MIRROR] if service == 'simbad' else [SERVICES[service]]
    for url in urls:
        try:
            response = httpx.get(url, params=dict(REQUEST='doQuery', LANG='ADQL',
                                QUERY=query, FORMAT='votable', MAXREC='501'), timeout=20)
            response.raise_for_status()
            if len(response.content) > 5*1024*1024:
                raise ValueError('Przekroczony limit odpowiedzi katalogowej.')
            table = parse_single_table(io.BytesIO(response.content)).to_table(use_names_over_ids=True)
            table.meta['service_url'] = url
            break
        except (httpx.HTTPError, ValueError) as exc:
            error = exc
    if table is None:
        raise error or ValueError('Brak odpowiedzi katalogu.')
    rows = CatalogRows(table.meta['service_url'], response.content)
    for row in table:
        item = {}
        for name in table.colnames:
            value = row[name]
            if np.ma.is_masked(value):
                item[name.lower()] = None
            elif isinstance(value, (np.floating, float)):
                item[name.lower()] = float(value) if np.isfinite(value) else None
            elif isinstance(value, (np.integer, int)):
                item[name.lower()] = int(value)
            else:
                item[name.lower()] = str(value)
        rows.append(item)
    return rows


def allwise_gator(ra, dec, radius_arcsec):
    url = 'https://irsa.ipac.caltech.edu/cgi-bin/Gator/nph-query'
    response = httpx.get(url, params=dict(catalog='allwise_p3as_psd', spatial='Cone',
                         objstr=f'{ra} {dec}', radius=radius_arcsec, radunits='arcsec', outfmt=1,
                         selcols='designation,ra,dec,w1mpro,w2mpro,w3mpro,w4mpro,cc_flags,ph_qual'), timeout=25)
    response.raise_for_status()
    if len(response.content) > 5*1024*1024:
        raise ValueError('Przekroczony limit odpowiedzi AllWISE.')
    table = Table.read(response.text, format='ascii.ipac')
    rows = CatalogRows(url, response.content)
    for row in table[:501]:
        item = {}
        for name in table.colnames:
            value = row[name]
            if np.ma.is_masked(value): item[name] = None
            elif isinstance(value, (float, np.floating)): item[name] = float(value) if np.isfinite(value) else None
            else: item[name] = str(value)
        rows.append(item)
    return rows


def catalog_candidates(service, ra, dec, radius_arcsec, mjd):
    key = hashlib.sha256(json.dumps(['context-1', service, ra, dec, radius_arcsec, mjd]).encode()).hexdigest()
    saved = store.get('catalog_context', key)
    if saved:
        return saved
    # Wider ingress cone, with final filtering at the observation epoch.
    radius_deg = max(radius_arcsec, 120)/3600 if service == 'simbad' else radius_arcsec/3600
    cone = f"CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{ra:.12f},{dec:.12f},{radius_deg:.12f}))=1"
    if service == 'simbad':
        query = 'SELECT TOP 501 main_id,otype,sp_type,ra,dec,pmra,pmdec FROM basic WHERE '+cone
    else:
        query = 'SELECT TOP 501 designation,ra,dec,w1mpro,w2mpro,w3mpro,w4mpro,cc_flags,ph_qual FROM allwise_p3as_psd WHERE '+cone
    access = 'TAP (SIMBAD: serwer główny lub oficjalne lustro Harvard)' if service == 'simbad' else 'IRSA TAP'
    try:
        rows = tap(service, query)
    except Exception:
        if service != 'allwise': raise
        rows = allwise_gator(ra, dec, radius_arcsec)
        access = 'IRSA Gator'
    target = SkyCoord(ra, dec, unit='deg')
    candidates = []
    for row in rows[:500]:
        if row.get('ra') is None or row.get('dec') is None:
            continue
        coord = SkyCoord(row['ra'], row['dec'], unit='deg')
        propagated = False
        if service == 'simbad' and all(row.get(k) is not None for k in ('pmra', 'pmdec')):
            coord = SkyCoord(ra=coord.ra, dec=coord.dec, pm_ra_cosdec=row['pmra']*u.mas/u.yr,
                             pm_dec=row['pmdec']*u.mas/u.yr, obstime=Time(2000, format='jyear')).apply_space_motion(new_obstime=Time(mjd, format='mjd'))
            propagated = True
        distance = float(target.separation(coord).arcsec)
        if distance > radius_arcsec:
            continue
        candidates.append(dict(catalog=service, name=row.get('main_id') or row.get('designation'),
                               object_type=row.get('otype'), spectral_type=row.get('sp_type'),
                               ra=float(coord.ra.deg), dec=float(coord.dec.deg),
                               separation_arcsec=distance, propagated=propagated,
                               metadata=row))
    candidates.sort(key=lambda c: c['separation_arcsec'])
    result = dict(id=key, catalog=service, service_url=getattr(rows, 'source_url', SERVICES[service]), access=access,
                  response_sha256=getattr(rows, 'response_sha256', None),
                  mirror_url=SIMBAD_MIRROR if service == 'simbad' else None, candidates=candidates,
                  truncated=len(rows) >= 500, query=query, retrieved_at=datetime.now(timezone.utc).isoformat(),
                  position_note='SIMBAD J2000 + dostępny ruch własny' if service == 'simbad' else 'Historyczna pozycja AllWISE; bez propagacji ruchu')
    store.put('catalog_context', key, result)
    return result


def context(manifest, x, y, frame_id, radius_arcsec, progress=lambda i, n: None):
    source = source_record(manifest, x, y)
    frame = next((f for f in manifest['frames'] if f['id'] == frame_id), None)
    if frame is None:
        raise ValueError('Wybierz ekspozycję analizy.')
    position = dict(ra=source['ra'], dec=source['dec'], method='user_selected_point')
    centroid_warning = None
    try:
        from backend.native_diagnostics import native_profile
        fit = native_profile(manifest, x, y, frame_id)
        if fit['snr'] >= 5 and fit['reduced_chi2'] <= 3:
            position.update(ra=fit['ra'], dec=fit['dec'], method=fit['method'], error_arcsec=fit['error_arcsec'])
        else:
            centroid_warning = 'Dopasowanie pozycji nie spełnia progów; użyto kliknięcia.'
    except (ValueError, KeyError, OSError) as exc:
        centroid_warning = str(exc)
    results, failures = [], []
    for i, service in enumerate(('gaia', 'simbad', 'allwise')):
        progress(i, 3)
        try:
            if service == 'gaia':
                from backend.source_assessment import rank_matches
                cat = catalogs.gaia(position['ra'], position['dec'], max(2, radius_arcsec/60), frame['mjd'])
                results.append(dict(catalog='gaia', id=cat['id'], truncated=cat['truncated'],
                                    candidates=rank_matches(position['ra'], position['dec'], cat, radius_arcsec)))
            else:
                results.append(catalog_candidates(service, position['ra'], position['dec'], radius_arcsec, frame['mjd']))
        except Exception as exc:
            failures.append(dict(catalog=service, reason=f'{type(exc).__name__}: {exc}'[:300]))
    if not results:
        raise ValueError('Wszystkie katalogi są niedostępne. Spróbuj ponownie później.')
    wcs = WCS(manifest['wcs'])
    for catalog in results:
        for candidate in catalog['candidates']:
            px, py = wcs.world_to_pixel(SkyCoord(candidate['ra'], candidate['dec'], unit='deg'))
            point = dict(x=float((px+.5)/manifest['pixels']), y=float(1-(py+.5)/manifest['pixels']))
            candidate['point'] = point if 0 <= point['x'] <= 1 and 0 <= point['y'] <= 1 else None
    return dict(kind='context', analysis_id=manifest['id'], source_id=source['id'], point=source['point'],
                frame_id=frame_id, mjd=frame['mjd'], position=position, centroid_warning=centroid_warning,
                catalogs=results, failures=failures, method='multi-catalog-context-1', limitations=[
                    'Typ i klasa widmowa pochodzą z SIMBAD, nie z klasyfikacji zdjęcia przez aplikację.',
                    'Lista zawiera kandydatów. Nie łączymy automatycznie wpisów różnych katalogów w jeden obiekt.',
                    'AllWISE przedstawia historyczną pozycję. Ruch własny może uniemożliwić dopasowanie.',
                    'Brak paralaksy i pozycji pozornej; stożek wyszukiwania i limity mogą pominąć źródła.',
                    'Brak odpowiednika katalogowego nie potwierdza nowego obiektu.'])
