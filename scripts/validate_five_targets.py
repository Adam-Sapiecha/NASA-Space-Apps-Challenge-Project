"""Fresh, bounded DR1 audit at verified catalogue fields; no discovery claims.

Eight D2 images per field (D6 for WISE 0855). Keeps every partial failure, native
FITS and manifest; measures the *predicted* position at each individual epoch.
"""
import json
import sys
import uuid
import warnings
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from backend import archive, store
from backend.science import build_analysis
from backend.measurements import measure
from backend.targets import TARGETS, position


def spaced(rows, limit=8):
    if len(rows) <= limit:
        return rows
    chosen = {0, len(rows)-1}
    for t in np.linspace(rows[0]['mjd'], rows[-1]['mjd'], limit):
        chosen.add(min(range(len(rows)), key=lambda i: abs(rows[i]['mjd']-t)))
    return [rows[i] for i in sorted(chosen)]


def main():
    from astropy import log
    log.setLevel('ERROR')  # The documented alternate spectral WCS carries SIP cards.
    report = dict(checked_at=datetime.now(timezone.utc).isoformat(), targets=[],
                  method='eight-sampled-epochs-at-catalogue-predictions-1',
                  limitations=['Catalogue predictions do not establish SPHEREx source identification.',
                               'No parallax, perspective acceleration or binary orbital model.',
                               'WCS-WAVE compatibility is a browsing heuristic, not response calibration.'])
    path = store.ROOT/'audit'/'five-targets-final.json'
    path.parent.mkdir(exist_ok=True)
    for target in TARGETS:
        row = dict(target=target, status='inconclusive')
        print(target['name'], flush=True)
        try:
            source = archive.search(str(target['field_ra']), str(target['field_dec']), 6, 'spherex_dr1')
            source['id'] = uuid.uuid4().hex
            source['target_prediction'] = target
            store.put('search', source['id'], source)
            detector = 'SPHEREx-D6' if target['id']=='wise0855' else 'SPHEREx-D2'
            selected = spaced([o for o in source['observations'] if o['band']==detector])
            if not selected:
                raise ValueError('No products in selected detector.')
            id = uuid.uuid4().hex
            build_analysis(id, source, [o['id'] for o in selected])
            manifest = store.get('analysis', id)
            if not manifest:
                raise ValueError(store.get('job', id)['message'])
            row.update(analysis_id=id, archive_rows=source['archive_rows'], selected_detector=detector,
                       selected=len(selected), prepared=len(manifest['frames']), failures=manifest['failures'], samples=[])
            for frame in manifest['frames']:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    prediction = position(target, frame['mjd'])
                px,py = WCS(manifest['wcs']).world_to_pixel(SkyCoord(prediction['ra'],prediction['dec'],unit='deg'))
                n=manifest['pixels']; x,y=(float(px)+.5)/n,1-(float(py)+.5)/n
                sample = dict(frame_id=frame['id'],date=frame['date'],mjd=frame['mjd'],prediction=prediction,point=dict(x=x,y=y),coverage=frame['coverage'])
                if 0<=x<=1 and 0<=y<=1:
                    measurement=measure(manifest,x,y,12.4)
                    measured=next(r for r in measurement['rows'] if r['id']==frame['id'])
                    sample.update(measurement_id=measurement['id'],measurement=measured)
                else:
                    sample['measurement']=dict(valid=False,reason='Catalogue prediction outside cutout.')
                row['samples'].append(sample)
            good=[s for s in row['samples'] if s['measurement']['valid']]
            pairs=[]
            for i,a in enumerate(good):
                for b in good[i+1:]:
                    ar,br=a['measurement'],b['measurement']
                    if a['mjd']!=b['mjd'] and abs(ar['wavelength_um']-br['wavelength_um'])<=min(ar['bandwidth_um'],br['bandwidth_um'])/2:
                        pairs.append(dict(frame_ids=[a['frame_id'],b['frame_id']],days=abs(a['mjd']-b['mjd']),wavelengths_um=[ar['wavelength_um'],br['wavelength_um']]))
            row.update(valid_predicted_apertures=len(good), comparable_pairs=sorted(pairs,key=lambda p:-p['days']),
                       result='Real field images tested at catalogue-predicted positions. Source identification, motion and variability remain unconfirmed.')
        except Exception as exc:
            row.update(error=f'{type(exc).__name__}: {exc}')
        report['targets'].append(row)
        path.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        print({k:row[k] for k in ('analysis_id','archive_rows','prepared','valid_predicted_apertures','error') if k in row},flush=True)
    print(path,flush=True)


if __name__=='__main__':
    main()
