"""Integration check against a running API, using saved genuine SPHEREx FITS."""
import argparse
import json
from pathlib import Path

import httpx


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    source = json.loads(Path('data/smoke_api.json').read_text(encoding='utf-8'))
    with httpx.Client(base_url=args.base_url, timeout=60) as client:
        analysis = client.get(f"/api/analyses/{source['id']}").json()
        id = analysis['id']
        raw = client.post(f'/api/analyses/{id}/previews', json=dict(quality='all', range_mode='standard'))
        raw.raise_for_status()
        clean = client.post(f'/api/analyses/{id}/previews', json=dict(quality='valid', range_mode='standard'))
        clean.raise_for_status()
        for original, filtered in zip(raw.json()['frames'], clean.json()['frames']):
            assert original['display_coverage'] >= filtered['display_coverage']
            assert client.get(original['image']).content.startswith(b'\x89PNG')
            assert client.get(original['quality_image']).content.startswith(b'\x89PNG')
        geometry = client.get(f'/api/analyses/{id}/footprint'); geometry.raise_for_status()
        assert len(geometry.json()['footprint']) == 68
        result = client.post('/api/orientation', json=dict(ra=analysis['search']['ra'], dec=analysis['search']['dec'],
            latitude=52.23, longitude=21.01, utc=analysis['frames'][0]['date']+'Z'))
        result.raise_for_status(); assert result.json()['refraction'] is False
        measurement = client.post(f'/api/analyses/{id}/measurements', json=dict(x=.5, y=.5, radius_arcsec=12.4))
        measurement.raise_for_status(); m = measurement.json()
        assert len(m['rows']) == len(analysis['frames']) and any(r['valid'] for r in m['rows'])
        advice = client.get(f"/api/measurements/{m['id']}/recommendation").json()
        assert advice['weights'] is None
        payload = dict(operation='difference', frame_ids=[f['id'] for f in analysis['frames']], weights=[1,1], max_hours=24)
        response = client.post(f'/api/analyses/{id}/products', json=payload); response.raise_for_status()
        p = response.json()
        assert p['display']['low'] == -p['display']['high']
        assert client.get(p['image']).content.startswith(b'\x89PNG')
        assert client.get(f"/api/products/{p['id']}/image.fits").content.startswith(b'SIMPLE')
        assert client.get(f"/api/products/{p['id']}/manifest.json").json()['weights'] == [1,1]
        # A repeated request must restore an immutable product, including creation time.
        assert client.post(f'/api/analyses/{id}/products', json=payload).json() == p
        assert client.get('/').status_code == 200
        report = dict(status='passed', analysis_id=id, measurement_id=m['id'], product_id=p['id'],
                      checks=['full original pixel previews', 'separate warning overlay', 'WCS footprint', 'AltAz', 'native FITS aperture and variance', 'assistant validation guard',
                              'signed difference', 'PNG/FITS/manifest', 'immutable product replay', 'frontend'])
        Path('data/smoke_plan_v4.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report))


if __name__=='__main__':
    main()
