"""Verify the running local application, reusing a real calibration result.

Creates one genuine aperture measurement; does not import synthetic IRSA data.
"""
import json
from datetime import datetime,timezone
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parents[1]
ANALYSIS='4812094a2ce843a8b787837eb13ec845'
CALIBRATED='81560764686b47db8c178f47c55edd86'


def main():
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=90) as client:
        def get(path):
            r=client.get(path);r.raise_for_status();return r.json()
        health=get('/api/health');assert health['status']=='ok' and not health['code_changed']
        p=dict(x=.509,y=.507)
        sample=get(f'/api/analyses/{ANALYSIS}/sample?x={p["x"]}&y={p["y"]}')
        r=client.post(f'/api/analyses/{ANALYSIS}/measurements',json=dict(**p,radius_arcsec=12.4));r.raise_for_status();measurement=r.json()
        assert measurement['method']=='native-aperture-area-3'
        assert abs(sample['ra']-measurement['ra'])<1e-10 and abs(sample['dec']-measurement['dec'])<1e-10
        assert any(row['valid'] and row.get('calibration_sources') for row in measurement['rows'])
        cal=get('/api/irsa/results/'+CALIBRATED);assert cal['method']=='release-maps-epsf-2'
        assert all('position_sensitivity' in row and row['robustness']['status']=='requires_validation' for row in cal['rows'])
        expected=json.loads((ROOT/'data/audit/math_fixes_20261114/offline-validation.json').read_text())['real_wise']
        for a,b in zip(cal['rows'],expected['rows']):
            assert abs(a['epsf']['flux_mjy']-b['epsf']['flux_mjy'])<1e-10
            assert a['aperture']['valid']==b['aperture']['valid']
        # Archival reports remain readable but cannot enter a new quantitative chain.
        old=client.post(f'/api/analyses/{ANALYSIS}/reference',json=dict(calibrated_id='2136c5099162463189f514ddc83c44f0',format='csv',content='not used'))
        assert old.status_code==422 and 'Archiwalna' in old.json()['detail']
        card=get('/api/notes/a6971713a10c44bf8ca7045c5c748759/evidence')
        assert card['schema_version']==2 and all(s['point']==card['view']['point'] for s in card['sources'])
        assert card['measurement_position']['method']=='native-aperture-2'
        page=client.get('/api/notes/a6971713a10c44bf8ca7045c5c748759/evidence.html');page.raise_for_status()
        assert 'Photometry uses a fixed aperture at ICRS' in page.text
        assert get('/api/artifacts/status')['active_model'] is None
        result=dict(utc=datetime.now(timezone.utc).isoformat(),status='passed',health=health,measurement_id=measurement['id'],
                    calibrated_id=CALIBRATED,sample_point=p,coordinate_difference_deg=[sample['ra']-measurement['ra'],sample['dec']-measurement['dec']],
                    checks=['continuous point matches real aperture','per-pixel calibrated solid angle','live calibration equals offline real-FITS result',
                            'separate aperture/ePSF validity','position/background sensitivity','archival calibration blocked downstream',
                            'evidence marker and photometry positions explicit','no active unvalidated ML'],public_url_verified=False)
        (ROOT/'data/audit/math_fixes_20261114/live-validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
        print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
