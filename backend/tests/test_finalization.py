import base64
from concurrent.futures import Future
from datetime import datetime, timezone

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend import store, science, main
from backend.targets import TARGETS, position
from backend.measurements import aperture


@pytest.fixture(autouse=True)
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'ROOT', tmp_path)


def test_catalogue_identity_regression_and_independent_motion_estimate():
    by_id = {t['id']: t for t in TARGETS}
    # Published SIMBAD identities: old presets pointed at unrelated fields.
    assert by_id['r-dra']['ra_deg'] == pytest.approx(248.16761, abs=1e-5)
    assert by_id['epsilon-indi-b']['ra_deg'] == pytest.approx(331.04415, abs=1e-5)
    barnard = by_id['barnard']
    with pytest.warns(Warning):
        moved = position(barnard, barnard['epoch_mjd']+365.25)
    # Independent tangent-plane estimate, not a second call to the same helper.
    assert (moved['dec']-barnard['dec_deg'])*3600 == pytest.approx(10.362394, abs=.001)
    assert (moved['ra']-barnard['ra_deg'])*3600*np.cos(np.deg2rad(barnard['dec_deg'])) == pytest.approx(-.801551, abs=.001)
    wise = by_id['wise0855']
    assert wise['epoch_mjd'] == 57633.39
    assert wise['ra_deg'] == 133.780984


def test_known_source_contaminates_background_but_is_allowed_in_target():
    yy,xx=np.indices((51,51));distance=np.hypot(xx-25,yy-25)
    data=np.full((51,51),10.);variance=np.ones_like(data);flags=np.zeros_like(data,dtype=np.uint32)
    data[distance<=4]+=3
    flags[distance<=4]=1<<21
    data[25,35]=10000.;flags[25,35]=1<<21
    result=aperture(data,variance,flags,0,distance,4,background_mask=1<<21)
    assert result['background']==10
    assert result['aperture_sum']==3*np.sum(distance<=4)
    flags[(distance>=7.2)&(distance<=12)]=1<<21
    with pytest.raises(ValueError,match='pikseli tła'):
        aperture(data,variance,flags,0,distance,4,background_mask=1<<21)


def test_worker_process_loss_is_reported_and_submit_failure_is_503(monkeypatch):
    class DeadWorker:
        def submit(self,*args):
            future=Future();future.set_exception(RuntimeError('worker died'));return future
    monkeypatch.setattr(main,'pool',DeadWorker())
    main.submit_job('dead',lambda *args:None)
    assert store.get('job','dead')['status']=='failed'
    class UnavailableWorker:
        def submit(self,*args):raise RuntimeError('broken process pool')
    monkeypatch.setattr(main,'pool',UnavailableWorker())
    with pytest.raises(main.HTTPException) as exc:
        main.submit_job('unavailable',lambda *args:None)
    assert exc.value.status_code==503
    assert store.get('job','unavailable')['status']=='failed'


def test_portable_evidence_has_local_gaps_provenance_and_safe_human_text(tmp_path):
    id='analysis';folder=tmp_path/'analyses'/id;folder.mkdir(parents=True)
    # Deliberately controlled fixture, never presented as an archive observation.
    png=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aD1sAAAAASUVORK5CYII=')
    frames=[]
    for i in range(2):
        fid=str(i)*20
        (folder/f'{fid}.png').write_bytes(png)
        np.savez(folder/f'{fid}.npz',wavelength=np.full((2,2),np.nan if i else 1.),
                 bandwidth=np.full((2,2),.04),valid=np.full((2,2),not i),flags=np.zeros((2,2),dtype=np.uint32))
        frames.append(dict(id=fid,obs_id=f'test-{i}',date='2026-01-01',mjd=61041+i,band='D2',
                           wavelength_um=1.2,bandwidth_um=.04,flag_definitions={},sha256='a'*64,url='https://irsa.ipac.caltech.edu/ibe/data/spherex/test.fits',unit='MJy/sr'))
    manifest=dict(id=id,frames=frames,pixels=2,wcs=dict(science.output_wcs(42,0,2,2).to_header()),search={},display=dict(low=0,high=1))
    store.put('analysis',id,manifest)
    note=dict(id='note',analysis_id=id,created_at=datetime.now(timezone.utc).isoformat(),frame_ids=[f['id'] for f in frames],
              point=dict(x=.5,y=.5),kind='uncertain',text='<script>alert(1)</script>',anchors=[],route_checks={})
    store.put('note','note',note)
    with TestClient(main.app) as client:
        exported=client.get('/api/notes/note/evidence').json()
        assert exported['sources'][0]['wavelength_um']==1
        assert exported['sources'][1]['wavelength_um'] is None  # no centre fallback
        assert exported['sources'][1]['valid_at_point'] is False
        assert exported['sources'][0]['sha256']=='a'*64
        assert exported['diagnostics'] is None
        page=client.get('/api/notes/note/evidence.html')
        assert page.status_code==200
        assert '<script>' not in page.text
        assert '&lt;script&gt;' in page.text
        assert page.text.count('src="data:image/png;base64,')==2
        assert 'attachment;' in page.headers['content-disposition']
        assert client.get('/api/notes/missing/evidence').status_code==404
