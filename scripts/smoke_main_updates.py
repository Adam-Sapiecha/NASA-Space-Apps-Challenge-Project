"""Exercise the real automatic-selection queue and persist its result."""
import json
import time
from pathlib import Path
import httpx


def main():
    root=Path(__file__).resolve().parents[1]
    source=json.loads((root/'data/audit/five-targets-final.json').read_text(encoding='utf-8'))
    epsilon=next(t for t in source['targets'] if t['target']['id']=='epsilon-indi-b')
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=30) as client:
        health=client.get('/api/health').json()
        assert health['status']=='ok' and not health['code_changed'],health
        prior=client.get('/api/analyses/'+epsilon['analysis_id']);prior.raise_for_status()
        request=dict(search_id=prior.json()['search']['id'],target_id='epsilon-indi-b',candidate_limit=36)
        started=time.monotonic()
        queued=client.post('/api/analyses/auto',json=request);queued.raise_for_status()
        id=queued.json()['id'];print('Automatic job: '+id,flush=True)
        seen=set()
        for _ in range(450):
            response=client.get('/api/jobs/'+id);response.raise_for_status();job=response.json()
            key=(job['status'],job.get('completed'),job.get('total'))
            if key not in seen:print(job.get('message'),flush=True);seen.add(key)
            if job['status']=='failed':raise RuntimeError(job)
            if job['status']=='complete':break
            time.sleep(2)
        else:raise TimeoutError('Automatic selection did not finish within 15 minutes.')
        response=client.get('/api/analyses/'+id);response.raise_for_status();manifest=response.json()
        report=manifest['selection']
        assert report['method']=='target-local-selection-1'
        assert report['inspected']<=36 and 1<=len(manifest['frames'])<=8
        assert report['target_id']=='epsilon-indi-b'
        assert all(f['id'] in report['selected_ids'] for f in manifest['frames'])
        response=client.get('/api/selections/'+id);response.raise_for_status()
        assert response.json()['candidates']==report['candidates']
        for f in manifest['frames']:
            r=client.get(f['image']);r.raise_for_status();assert r.content.startswith(b'\x89PNG')
        export=client.get('/api/analyses/'+id+'/export');export.raise_for_status()
        assert export.json()['selection']==report
        output=dict(status='passed',health=health,analysis_id=id,selection_status=report['status'],
                    prepared=len(manifest['frames']),inspected=report['inspected'],
                    baseline_days=report.get('baseline_days'),elapsed_seconds=round(time.monotonic()-started,2),
                    checks=['current backend fingerprint','real process queue','bounded local FITS checks',
                            'target binding','prepared images','persistent selection report','manifest export'])
        (root/'data/audit/main-updates-api.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
        print(json.dumps(output,indent=2),flush=True)


if __name__=='__main__':main()
