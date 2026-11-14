"""Exercise lazy frame preparation and independent displays on real saved data."""
import hashlib
import json
import time
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx


def main():
    root=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(root))
    from backend import store
    with store.connect() as db:
        saved=[json.loads(row[0]) for row in db.execute("SELECT body FROM records WHERE kind='analysis'")]
    eligible=[row for row in saved if row.get('selection',{}).get('target_id')=='epsilon-indi-b' and not row.get('workspace')]
    id=max(eligible,key=lambda row:row.get('created_at',''))['id']
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=40) as client:
        health=client.get('/api/health').json();assert not health['code_changed']
        original=client.get('/api/analyses/'+id);original.raise_for_status();parent=original.json()
        ready={frame['id'] for frame in parent['frames']}
        candidates=parent['selection']['candidates']
        extra=next(row for row in candidates if row['id'] not in ready and row.get('native_fits_sha256') and row.get('spectral_valid') and row.get('has_image_data') and row['band']!=parent['frames'][0]['band'])
        requested=[parent['frames'][0]['id'],extra['id']]
        started=time.monotonic()
        response=client.post(f'/api/analyses/{id}/comparison',json=dict(observation_ids=requested,previous_ids=[frame['id'] for frame in parent['frames'][:2]]));response.raise_for_status()
        job=response.json()['id'];print('Comparison job: '+job,flush=True)
        for _ in range(180):
            status=client.get('/api/jobs/'+job).json()
            if status['status']=='failed':raise RuntimeError(status)
            if status['status']=='complete':break
            time.sleep(.5)
        else:raise TimeoutError('Comparison did not finish')
        response=client.get('/api/analyses/'+job);response.raise_for_status();result=response.json()
        assert set(requested)<={frame['id'] for frame in result['frames']},result['failures']
        assert result['pixels']==parent['pixels'] and result['wcs']==parent['wcs']
        assert result['workspace']['recommended_pair_ids']==parent['selection']['pair_ids']
        assert result['workspace']['requested_ids']==requested
        assert client.get('/api/analyses/'+id).content==original.content
        cached=client.post(f'/api/analyses/{job}/comparison',json=dict(observation_ids=requested));cached.raise_for_status()
        assert cached.json()==dict(analysis_id=job,status='ready')
        def preview(settings):
            response=client.post(f'/api/analyses/{job}/previews',json=settings);response.raise_for_status();return response.json()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(preview,dict(quality='all',range_mode='standard',frame_ids=requested)),pool.submit(preview,dict(quality='valid',range_mode='faint',frame_ids=[requested[0]]))]
            displays=[future.result() for future in futures]
        assert len(displays[0]['frames'])==2 and len(displays[1]['frames'])==1
        assert displays[0]['id']!=displays[1]['id']
        for display in displays:
            for frame in display['frames']:
                image=client.get(frame['image']);image.raise_for_status();assert image.content.startswith(b'\x89PNG')
        assert client.post(f'/api/analyses/{job}/comparison',json=dict(observation_ids=['foreign'])).status_code==422
        output=dict(status='passed',analysis_id=job,root_analysis_id=id,requested=requested,
                    prepared=len(result['frames']),available_observations=len(result['search']['observations']),
                    recommended=result['workspace']['recommended_pair_ids'],elapsed_seconds=round(time.monotonic()-started,2),health=health,
                    checks=['lazy preparation','same sky geometry','unchanged original result','recommended defaults retained','ready comparison reused','independent preview settings','PNG responses','foreign observation rejected'])
        (root/'data/audit/combined-workspace.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
        print(json.dumps(output,indent=2),flush=True)


if __name__=='__main__':main()
