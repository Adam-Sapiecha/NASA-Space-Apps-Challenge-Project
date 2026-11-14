"""Import an exported IRSA spectrophotometry table and match actual exposures."""
import hashlib
import io
import json
import re
from xml.etree import ElementTree

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io.votable import parse
from astropy.table import Table

from backend import store


def read_reference(content, format):
    encoded=content.encode('utf-8')
    if len(encoded)>3*1024*1024: raise ValueError('Limit eksportu to 3 MB.')
    if format=='votable':
        if b'<!doctype' in encoded.lower() or b'<!entity' in encoded.lower():
            raise ValueError('Eksport nie może zawierać deklaracji zewnętrznych XML.')
        try:
            root=ElementTree.fromstring(encoded)
        except ElementTree.ParseError as exc:
            raise ValueError('Niepoprawny XML eksportu widma.') from exc
        if any(e.tag.rsplit('}',1)[-1]=='STREAM' and any(k.rsplit('}',1)[-1]=='href' for k in e.attrib) for e in root.iter()):
            raise ValueError('Wczytaj samodzielny eksport, bez odsyłaczy do zewnętrznych danych.')
        parsed=parse(io.BytesIO(encoded))
        candidates=[t.to_table(use_names_over_ids=True) for t in parsed.iter_tables()]
        tables=[t for t in candidates if {'wavelength','flux','flux_err'}<=set(t.colnames)]
        if len(tables)!=1: raise ValueError('Wybierz plik widma, nie listę źródeł. Wymagana jedna tabela wavelength/flux/flux_err.')
        table=tables[0]
    elif format=='csv':
        table=Table.read(io.BytesIO(encoded),format='ascii.csv')
    else:
        raise ValueError('Obsługiwane eksporty: VOTable XML i CSV.')
    required={'wavelength','flux','flux_err','mjd','ra','dec','det_id'}
    if not required<=set(table.colnames):
        raise ValueError('Brakuje kolumn porównania: '+', '.join(sorted(required-set(table.colnames))))
    flux_factor=u.Unit(table['flux'].unit or u.uJy).to(u.mJy)
    error_factor=u.Unit(table['flux_err'].unit or u.uJy).to(u.mJy)
    wave_factor=u.Unit(table['wavelength'].unit or u.um).to(u.um)
    width_factor=u.Unit(table['lambda_width'].unit or u.um).to(u.um) if 'lambda_width' in table.colnames else None
    ra_factor=u.Unit(table['ra'].unit or u.deg).to(u.deg)
    dec_factor=u.Unit(table['dec'].unit or u.deg).to(u.deg)
    time_factor=u.Unit(table['mjd'].unit or u.day).to(u.day)
    rows=[]
    for row in table:
        cells={k:np.atleast_1d(row[k]) for k in table.colnames}
        length=max(len(v) for v in cells.values())
        if any(len(v) not in (1,length) for v in cells.values()): raise ValueError('Niezgodne długości tablic widma.')
        for i in range(length):
            def value(k,default=None):
                if k not in cells:return default
                item=cells[k][0 if len(cells[k])==1 else i]
                return None if np.ma.is_masked(item) else item
            try:
                detector_value=float(value('det_id'))
                if not np.isfinite(detector_value) or detector_value!=int(detector_value) or not 1<=detector_value<=6:
                    raise ValueError('Niepoprawny identyfikator detektora.')
                entry=dict(wavelength_um=float(value('wavelength'))*wave_factor,flux_mjy=float(value('flux'))*flux_factor,
                           error_mjy=float(value('flux_err'))*error_factor,mjd=float(value('mjd'))*time_factor,
                           ra=float(value('ra'))*ra_factor,dec=float(value('dec'))*dec_factor,detector=int(detector_value),
                           bandwidth_um=float(value('lambda_width'))*width_factor if width_factor is not None and value('lambda_width') is not None else None,
                           lvf_id=str(value('lvf_id') or '').strip(),flags=int(value('flags',0)),
                           collection=str(value('data_collection') or '').strip().lower().removeprefix('spherex_'))
                if not all(np.isfinite(entry[k]) for k in ('wavelength_um','flux_mjy','error_mjy','mjd','ra','dec')) or entry['error_mjy']<=0 or entry['wavelength_um']<=0 or not 0<=entry['ra']<360 or not -90<=entry['dec']<=90:
                    raise ValueError('Niepoprawne wartości widma.')
                if entry['bandwidth_um'] is not None and (not np.isfinite(entry['bandwidth_um']) or entry['bandwidth_um']<=0):
                    raise ValueError('Niepoprawna szerokość pasma.')
                rows.append(entry)
            except (ValueError,TypeError,OverflowError):
                raise ValueError('Eksport zawiera brakujące lub niepoprawne wartości; odfiltruj wadliwe wiersze w IRSA.')
            if len(rows)>20000: raise ValueError('Limit to 20 000 pomiarów widma.')
    return rows,hashlib.sha256(encoded).hexdigest()


def compare_reference(local,manifest,content,format):
    from backend.calibrated import require_current_report
    require_current_report(local)
    rows,sha=read_reference(content,format)
    target=SkyCoord(local['ra'],local['dec'],unit='deg')
    matches=[]
    def exposure_id(value):
        text=str(value or '').strip()
        match=re.search(r'(\d{4}W\d{2}_[12][AB]_\d{4}_[1-4])(?:D[1-6])?',text)
        return match.group(1) if match else text
    for frame in manifest['frames']:
        local_row=next((r for r in local['rows'] if r['id']==frame['id']),None)
        found=[]; reasons=[]
        detector=int(frame['band'].rsplit('D',1)[-1])
        start=frame.get('start_mjd',frame['mjd'])-1/86400
        end=frame.get('end_mjd',frame['mjd'])+1/86400
        for idx,row in enumerate(rows):
            if row['detector']!=detector or not start<=row['mjd']<=end:continue
            if SkyCoord(row['ra'],row['dec'],unit='deg').separation(target).arcsec>2:continue
            if not row['collection'] or row['collection']!=manifest['search']['collection'].removeprefix('spherex_'):
                reasons.append('Brak lub niezgodne wydanie data_collection.');continue
            expected_id=exposure_id(frame.get('obs_id'))
            embedded_detector=re.search(r'\d{4}W\d{2}_[12][AB]_\d{4}_[1-4]D([1-6])',row['lvf_id'])
            if embedded_detector and int(embedded_detector.group(1))!=detector:
                reasons.append('Detektor w lvf_id jest niezgodny z det_id.');continue
            if not expected_id or not row['lvf_id'] or exposure_id(row['lvf_id'])!=expected_id:
                reasons.append('Brak lub niezgodny identyfikator ekspozycji lvf_id.');continue
            if not local_row or not local_row.get('valid') or local_row.get('epsf',{}).get('valid') is False:
                reasons.append('Brak ważnego lokalnego ePSF.');continue
            wl,bw=local_row.get('wavelength_um'),local_row.get('bandwidth_um')
            if wl is None or bw is None or row['bandwidth_um'] is None:
                reasons.append('Brak lokalnego pasma lub lambda_width referencji.');continue
            # Consistency of metadata for the same exposure, not proof of equal response curves.
            if abs(row['wavelength_um']-wl)>max(.0001,min(.003,bw*.1)) or abs(row['bandwidth_um']-bw)>max(.003,bw*.15):
                reasons.append('Niezgodna długość fali lub szerokość pasma.');continue
            found.append((idx,row))
        if len(found)!=1 or not local_row or not local_row['valid']:
            matches.append(dict(frame_id=frame['id'],matched=False,reason=' '.join(sorted(set(reasons))) or 'Brak jednoznacznego pomiaru ekspozycji, detektora i pozycji lub brak ważnego lokalnego pomiaru.'))
            continue
        index,row=found[0]
        delta=local_row['epsf']['flux_mjy']-row['flux_mjy']
        matches.append(dict(frame_id=frame['id'],matched=True,status='metadata_match_only',reference_row=index,date=frame['date'],
                            wavelength_um=row['wavelength_um'],reference_flux_mjy=row['flux_mjy'],
                            reference_error_mjy=row['error_mjy'],reference_flags=row['flags'],
                            local_epsf_flux_mjy=local_row['epsf']['flux_mjy'],local_aperture_flux_mjy=local_row.get('aperture_flux_mjy'),
                            difference_mjy=delta,reference_lvf_id=row['lvf_id']))
    id=hashlib.sha256((local['id']+sha+'reference-2').encode()).hexdigest()
    result=dict(id=id,kind='reference',calibrated_result_id=local['id'],analysis_id=manifest['id'],
                input_sha256=sha,origin='user_supplied_export_declared_as_IRSA',rows=rows,matches=matches,
                matched_count=sum(r['matched'] for r in matches),
                method='reference-metadata-2',csv_units='IRSA schema: wavelength/lambda_width µm, flux/flux_err µJy, RA/Dec deg, MJD days; VOTable uses declared units',
                limitations=['Format i zgodność metadanych nie dowodzą pochodzenia pliku. Zachowano jego SHA-256.',
                             'Porównujemy tylko jednoznacznie dopasowane ekspozycje, detektory, wydania i pozycje (do 2″).',
                             'Wymagamy lvf_id, data_collection, wavelength i lambda_width. Tolerancje metadanych nie potwierdzają pełnej zgodności odpowiedzi pasma.',
                             'Pomiar apertury i dopasowanie ePSF mogą różnić się od IRSA Tractor przez tło, sąsiadów, normalizację i kalibrację.',
                             'Nie obliczamy istotności różnicy: metody korzystają z tych samych danych i mają skorelowane błędy.'])
    store.put('irsa_result',id,result)
    return result
