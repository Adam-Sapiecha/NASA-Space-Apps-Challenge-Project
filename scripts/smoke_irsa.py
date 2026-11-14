"""Check the live local API against real cached FITS and official IRSA services.

Start the application first. This creates local jobs and downloads bounded HiPS
images/calibrations; it does not submit an IRSA spectrophotometry computation.
"""
import json
import sys
import time
from pathlib import Path

import httpx

ROOT=Path(__file__).resolve().parents[1]


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('base',nargs='?',default='http://127.0.0.1:8000')
    parser.add_argument('--analysis')
    parser.add_argument('--x',type=float,default=.5)
    parser.add_argument('--y',type=float,default=.5)
    args=parser.parse_args()
    base=args.base
    analysis=args.analysis or json.loads((ROOT/'data/smoke_api.json').read_text())['id']
    with httpx.Client(base_url=base,timeout=120) as client:
        def get(path):
            response=client.get(path);response.raise_for_status();return response
        manifest=get(f'/api/analyses/{analysis}').json()
        metadata=get('/api/irsa/hips').json()
        assert len(metadata['layers'])==102
        for path in ['/api/irsa/hips/layers/29/Norder0/Dir0/Npix0.png',
                     '/api/irsa/hips/layers/29/Norder3/Allsky.png']:
            assert get(path).content.startswith(b'\x89PNG')
        assert client.get('/api/irsa/hips/layers/50/properties').status_code==404
        jobs={}
        for kind,path,payload in [
            ('calibrated',f'/api/analyses/{analysis}/calibrated',dict(x=args.x,y=args.y,radius_arcsec=12.4)),
            ('discovery',f'/api/analyses/{analysis}/discovery',dict(frame_id=manifest['frames'][0]['id'],threshold=5,minarea=3)),
            ('most','/api/irsa/most',dict(name='3I',start_date='2025-08-01',end_date='2025-08-20'))]:
            response=client.post(path,json=payload);response.raise_for_status()
            assert response.status_code==202
            jobs[kind]=response.json()['id']
        pending=dict(jobs);results={};deadline=time.monotonic()+240
        while pending:
            for kind,id in list(pending.items()):
                status=get(f'/api/jobs/{id}').json()
                if status['status']=='failed':raise RuntimeError(status['message'])
                if status['status']=='complete':
                    results[kind]=get(f'/api/irsa/results/{id}').json()
                    del pending[kind]
                    print(kind,id,'complete',flush=True)
            if pending:
                if time.monotonic()>deadline:raise TimeoutError('Jobs are still running; inspect /api/jobs/{id}.')
                time.sleep(1)
        assert any(r['valid'] for r in results['calibrated']['rows'])
        assert results['discovery']['detected_count']>=0
        assert all(0<=c['point']['x']<=1 and 0<=c['point']['y']<=1 for c in results['discovery']['candidates'])
        assert 'ra' in get(f"/api/irsa/results/{jobs['calibrated']}/target.tbl").text
        summary=dict(analysis_id=analysis,jobs=jobs,hips_layers=len(metadata['layers']),
                     valid_calibrated_rows=sum(r['valid'] for r in results['calibrated']['rows']),
                     candidates=results['discovery']['detected_count'],most_matches=results['most']['count'])
        (ROOT/'data/smoke_irsa_api.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
        print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
