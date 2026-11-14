"""Check a local or deployed URL without creating costly archive jobs."""
import argparse
import json
import time
from pathlib import Path

import httpx


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('base',nargs='?',default='http://127.0.0.1:8000')
    parser.add_argument('--analysis',default='4812094a2ce843a8b787837eb13ec845')
    parser.add_argument('--note',default='a6971713a10c44bf8ca7045c5c748759')
    parser.add_argument('--output',default='data/audit/submission-smoke.json')
    args=parser.parse_args()
    started=time.monotonic()
    with httpx.Client(base_url=args.base,timeout=90) as c:
        def get(path):
            r=c.get(path);r.raise_for_status();return r
        health=get('/api/health').json()
        assert health['status']=='ok' and not health['code_changed'],health
        paths=get('/openapi.json').json()['paths']
        for path in ('/api/targets','/api/irsa/hips','/api/analyses/{id}/calibrated','/api/analyses/{id}/discovery','/api/irsa/most','/api/analyses/{id}/reference','/api/notes/{id}/evidence.html'):
            assert path in paths,path
        assert c.post('/api/search',json=dict(ra='nan',dec='0')).status_code==422
        assert c.post('/api/search',json=dict(ra='42',dec='0',collection='unknown')).status_code==422
        assert c.get('/api/analyses/missing').status_code==404
        degrees=c.post('/api/field',json=dict(ra='270',dec='-7.5',fov_arcmin=4));degrees.raise_for_status()
        hours=c.post('/api/field',json=dict(ra='18:00:00',dec='-07:30:00',fov_arcmin=4));hours.raise_for_status()
        assert abs(degrees.json()['ra']-hours.json()['ra'])<1e-8
        assert abs(degrees.json()['dec']-hours.json()['dec'])<1e-8
        manifest=get('/api/analyses/'+args.analysis).json()
        assert manifest['frames'] and len({f['unit'] for f in manifest['frames']})==1
        for f in manifest['frames']:
            assert get(f['image']).content.startswith(b'\x89PNG')
            assert len(f['sha256'])==64
        note=get('/api/notes/'+args.note).json()
        assert note['analysis_id']==args.analysis and note['point']
        evidence=get('/api/notes/'+args.note+'/evidence').json()
        assert evidence['measurement']['point']==note['point']
        assert get('/api/notes/'+args.note+'/evidence.html').text.count('src="data:image/png;base64,')==2
        for page in ('/','/demo/','/demo/evidence.html'):
            assert get(page).status_code==200
        result=dict(status='passed',base=args.base,health=health,frames=len(manifest['frames']),note_id=args.note,
                    checks=['loaded code fingerprint','IRSA API schema','invalid coordinates 422','unknown collection 422','missing analysis 404',
                            'degree/hourangle equivalence','real saved PNG and provenance','saved note and same-point measurement',
                            'portable English evidence','English offline demo'],elapsed_seconds=round(time.monotonic()-started,2),
                    public_url_verified=not any(v in args.base for v in ('127.0.0.1','localhost','[::1]')))
        output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps(result,indent=2))


if __name__=='__main__':main()
