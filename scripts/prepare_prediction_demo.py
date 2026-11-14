"""Prepare four real visits, reserving the final visit for a temporal test."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from backend import store
from backend.science import build_analysis

IDENT='prediction3iatlas20251214d6'


def main():
    source_path=Path(__file__).resolve().parents[1]/'frontend/public/motion-demo/most-response.json'
    source=json.loads(source_path.read_text())
    ids=('2025W50_2A_0741_2','2025W50_2A_0755_2','2025W50_2A_0797_2','2025W50_2A_0813_2')
    rows=sorted([r for r in source['rows'] if r['productid']=='D6' and r['observationid'] in ids],key=lambda r:r['mjd_start'])
    if len(rows)!=4:raise ValueError('Four distinct recorded visits are required.')
    observations=[];priors=[]
    for r in rows:
        url='https://irsa.ipac.caltech.edu/'+r['uri'];fid=hashlib.sha256(url.encode()).hexdigest()[:20]
        mjd=(r['mjd_start']+r['mjd_end'])/2
        observations.append(dict(id=fid,obs_id=r['observationid'],url=url,mjd=mjd,
            date=r['start_date'].replace(' ','T'),band='SPHEREx-D6',collection='spherex_dr1',em_min_um=4.4115,em_max_um=5.0096))
        priors.append(dict(frame_id=fid,mjd=mjd,ra=r['ra_obj'],dec=r['dec_obj']))
    search=dict(id=IDENT,ra=float(np.mean([r['ra_obj'] for r in rows])),dec=float(np.mean([r['dec_obj'] for r in rows])),
        fov_arcmin=30,collection='spherex_dr1',observations=observations,
        note='Known 3I/ATLAS visits from IRSA MOST. Final visit is reserved for temporal validation.')
    if not store.get('analysis',IDENT):
        store.put('search',IDENT,search)
        print('Preparing four public IRSA products',flush=True)
        build_analysis(IDENT,search,[f['id'] for f in observations])
    m=store.get('analysis',IDENT)
    if not m or len(m['frames'])!=4:raise ValueError(str(store.get('job',IDENT)))
    m['motion_target']=dict(name='3I/ATLAS',source=source['source'],positions=priors,
        source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
        usage='Ephemerides constrain source association only; image centroids provide fitted positions.')
    (store.ROOT/'analyses'/IDENT/'manifest.json').write_text(json.dumps(m,indent=2,allow_nan=False),encoding='utf-8')
    store.put('analysis',IDENT,m)
    print(json.dumps(dict(id=IDENT,frames=[f['date'] for f in m['frames']])),flush=True)


if __name__=='__main__':main()
