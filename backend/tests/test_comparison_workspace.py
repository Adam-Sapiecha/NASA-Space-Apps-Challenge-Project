"""Custom pairs share sky geometry and reuse data without altering prior results."""
import hashlib

import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend import main,science,store
from backend.comparison_api import MAX_READY_FRAMES,prepare_comparison,workspace_plan


@pytest.fixture
def field(tmp_path,monkeypatch):
    monkeypatch.setattr(store,'ROOT',tmp_path)
    monkeypatch.setattr(science,'ROOT',tmp_path)
    observations=[dict(id=f'{i:020x}',mjd=61000+i,date=f'2026-01-0{i+1}T00:00:00',band='D1' if i<2 else 'D4',
                       url=f'https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/{i}.fits') for i in range(4)]
    source=dict(id='search',ra=42,dec=0,fov_arcmin=2,observations=observations)
    native=tmp_path/'native.fits';native.write_bytes(b'controlled native fixture')
    calls=[]
    def download(obs,*args,**kwargs):
        calls.append(obs['id'])
        if obs['id']==observations[3]['id']:raise TimeoutError('controlled archive failure')
        return native
    def read(path,coord,wcs,pixels):
        image=np.arange(pixels*pixels,dtype=float).reshape(pixels,pixels)
        return image,np.zeros_like(image,dtype=np.uint32),image*0+1,image*0+.04,dict(unit='MJy/sr',wavelength_um=1.,bandwidth_um=.04,coverage=1.,flag_definitions={},masked_flags=[])
    monkeypatch.setattr(science,'download',download);monkeypatch.setattr(science,'read_frame',read)
    recommended=[row['id'] for row in observations[:2]]
    report=dict(selected_ids=recommended,pair_ids=recommended,candidates=[],status='aperture_pair_available')
    science.build_analysis('root',source,recommended,selection=report)
    calls.clear()
    return tmp_path,store.get('analysis','root'),observations,calls


def test_extension_prepares_only_missing_frame_and_keeps_recommended_default(field):
    root,parent,observations,calls=field
    ids=[row['id'] for row in observations]
    original=hashlib.sha256((root/'analyses/root/manifest.json').read_bytes()).hexdigest()
    cache=root/'analyses/root'/f'{ids[0]}.display.npz';np.savez_compressed(cache,image=np.ones((32,32)),warned=np.zeros((32,32),bool))
    prepare_comparison('extended',parent,[ids[0],ids[2]],[ids[0],ids[1]])
    result=store.get('analysis','extended')
    assert calls==[ids[2]]
    assert result['workspace']['requested_ids']==[ids[0],ids[2]]
    assert result['workspace']['recommended_pair_ids']==ids[:2]
    assert result['workspace']['root_analysis_id']=='root'
    assert {frame['id'] for frame in result['frames']}==set(ids[:3])
    assert result['wcs']==parent['wcs'] and result['pixels']==parent['pixels']
    assert (root/'analyses/extended'/cache.name).read_bytes()==cache.read_bytes()
    assert hashlib.sha256((root/'analyses/root/manifest.json').read_bytes()).hexdigest()==original
    assert len(store.get('analysis','root')['frames'])==2


def test_failed_requested_image_retains_previous_pair_and_explicit_failure(field):
    _,parent,observations,_=field;ids=[row['id'] for row in observations]
    prepare_comparison('failed-image',parent,[ids[0],ids[3]],ids[:2])
    result=store.get('analysis','failed-image')
    assert store.get('job','failed-image')['status']=='complete'
    assert {frame['id'] for frame in result['frames']}==set(ids[:2])
    assert result['workspace']['requested_ids']==[ids[0],ids[3]]
    assert result['failures'][0]['observation']==ids[3]
    assert 'controlled archive failure' in result['failures'][0]['error']


def test_same_observation_can_be_displayed_twice_without_duplicate_download(field):
    _,parent,observations,calls=field;id=observations[2]['id']
    prepare_comparison('same',parent,[id,id])
    result=store.get('analysis','same')
    assert calls==[id] and result['workspace']['requested_ids']==[id,id]
    assert sum(frame['id']==id for frame in result['frames'])==1


def test_comparison_api_binds_source_and_reuses_ready_workspace(field,monkeypatch):
    _,parent,observations,_=field;ids=[row['id'] for row in observations]
    prepare_comparison('ready',parent,ids[:2])
    queued=[];monkeypatch.setattr(main,'submit_job',lambda *args:queued.append(args))
    with TestClient(main.app) as client:
        assert client.post('/api/analyses/ready/comparison',json={'observation_ids':ids[:2]}).json()==dict(analysis_id='ready',status='ready')
        assert not queued
        assert client.post('/api/analyses/ready/comparison',json={'observation_ids':['foreign']}).status_code==422
        assert client.post('/api/analyses/ready/comparison',json={'observation_ids':[ids[0]],'previous_ids':['foreign']}).status_code==422
        response=client.post('/api/analyses/ready/comparison',json={'observation_ids':[ids[2],ids[2]]})
        assert response.status_code==202 and queued[0][1] is prepare_comparison
        assert client.post('/api/analyses/ready/comparison',json={'observation_ids':[ids[2]]*13}).status_code==422


def test_bounded_ready_cache_keeps_defaults_and_current_pair_but_accepts_any_archive_id():
    rows=[dict(id=str(i)) for i in range(200)]
    parent=dict(id='root',frames=rows[:48],search=dict(observations=rows),selection=dict(selected_ids=['0','1'],pair_ids=['0','1']))
    retained,workspace=workspace_plan(parent,['198','199'],['2','3'])
    assert len(retained)==MAX_READY_FRAMES
    assert {'0','1','2','3','198','199'}<=set(retained)
    assert workspace['available_observations']==200
