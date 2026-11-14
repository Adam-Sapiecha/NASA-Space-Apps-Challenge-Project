import uuid
import pytest
from fastapi.testclient import TestClient
from astropy.table import Table

from backend import archive, store
from backend.main import app

@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(store,"ROOT",tmp_path)

def test_search_retains_simultaneous_detector_images(monkeypatch):
    table = Table(dict(access_url=[f"https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/D{i}.fits" for i in (1,2)],
                       obs_id=["same-exposure","same-exposure"],t_min=[60000.,60000.],t_max=[60000.1,60000.1],
                       energy_bandpassname=["SPHEREx-D1","SPHEREx-D2"],em_min=[.75e-6,1.1e-6],em_max=[1.09e-6,1.62e-6]))
    monkeypatch.setattr(archive,"query_images",lambda **kwargs: table)
    result = archive.search("42","0",12,"spherex_dr1")
    assert len(result["observations"]) == 2
    assert len({o["id"] for o in result["observations"]}) == 2

def test_api_reports_archive_failure_without_fake_images(monkeypatch):
    def fail(**kwargs):
        raise TimeoutError("archive unavailable")
    monkeypatch.setattr(archive,"search",fail)
    with TestClient(app) as client:
        result = client.post("/api/search",json=dict(ra="42",dec="0"))
        assert result.status_code == 502
        assert "IRSA" in result.json()["detail"]
        assert "Nie mamy zapisanej listy" in result.json()["detail"]
        assert "archive unavailable" not in result.json()["detail"]


def test_archive_outage_reuses_only_the_same_saved_field(monkeypatch):
    saved = dict(id='saved', ra=42., dec=0., fov_arcmin=12,
                 collection='spherex_dr1', retrieved_at='2026-11-14T10:00:00Z',
                 observations=[dict(id='real-archive-image')])
    store.put('search', 'saved', saved)
    def fail(**kwargs):
        raise TimeoutError('archive unavailable')
    monkeypatch.setattr(archive, 'search', fail)
    with TestClient(app) as client:
        result = client.post('/api/search', json=dict(ra='42', dec='0', fov_arcmin=12))
        assert result.status_code == 200
        assert result.json()['cached'] is True
        assert result.json()['observations'] == saved['observations']
        assert result.json()['retrieved_at'] == saved['retrieved_at']
        for override in [dict(ra='43'), dict(dec='1'), dict(collection='spherex_qr3')]:
            body = dict(ra='42', dec='0', fov_arcmin=12, collection='spherex_dr1') | override
            assert client.post('/api/search', json=body).status_code == 502


def test_outage_recovers_rounded_barnard_field_without_inventing_larger_coverage(monkeypatch):
    from backend import main
    saved=dict(id='barnard-real',ra=269.44626788,dec=4.76820441,fov_arcmin=6,
        collection='spherex_dr1',observations=[dict(id='actual-product')])
    store.put('search',saved['id'],saved)
    def fail(**kwargs):raise TimeoutError('502 Proxy Error')
    monkeypatch.setattr(archive,'search',fail)
    with TestClient(app) as client:
        result=client.post('/api/search',json=dict(ra='269.446',dec='4.7682',fov_arcmin=12))
        assert result.status_code==200
        body=result.json()
        assert body['id']==saved['id']
        assert (body['ra'],body['dec'],body['fov_arcmin'])==(saved['ra'],saved['dec'],6)
        assert body['observations']==saved['observations']
        assert body['requested_field']['fov_arcmin']==12
        assert '12′' in body['notice'] and '6′' in body['notice']
        assert body['cached'] is True
        # A nearby but distinct position beyond the rounding tolerance is refused.
        assert client.post('/api/search',json=dict(ra='269.447',dec='4.7682',fov_arcmin=12)).status_code==502


def test_cache_prefers_matching_extent_and_ignores_empty_searches():
    from backend import main
    common=dict(ra=42.,dec=0.,collection='spherex_dr1',observations=[dict(id='real')])
    store.put('search','matching',dict(common,id='matching',fov_arcmin=12))
    store.put('search','smaller',dict(common,id='smaller',fov_arcmin=6))
    store.put('search','empty',dict(common,id='empty',fov_arcmin=12,observations=[]))
    assert main.cached_search(main.SearchRequest(ra='42',dec='0',fov_arcmin=12))['id']=='matching'


def test_archive_http_requests_have_an_effective_timeout(monkeypatch):
    import requests
    captured = {}
    def request(self, method, url, **kwargs):
        captured.update(kwargs)
        return 'response'
    monkeypatch.setattr(requests.Session, 'request', request)
    with archive.ArchiveSession() as session:
        assert session.get('https://irsa.ipac.caltech.edu/SIA', timeout=None) == 'response'
    assert captured['timeout'] == (5, 20)

def test_api_rejects_invalid_requests_and_unknown_files():
    with TestClient(app) as client:
        assert client.post("/api/search",json=dict(ra="42",dec="0",fov_arcmin=1000)).status_code == 422
        assert client.post("/api/search",json=dict(ra="nan",dec="0")).status_code == 422
        assert client.get("/api/analyses/missing").status_code == 404

def test_duplicate_observation_selection_is_rejected():
    id = uuid.uuid4().hex
    store.put("search",id,dict(observations=[dict(id="test")]))
    with TestClient(app) as client:
        response = client.post("/api/analyses",json=dict(search_id=id,observation_ids=["test","test"]))
        assert response.status_code == 422


def test_examples_only_include_available_real_products(tmp_path):
    import json
    (tmp_path/'smoke_api.json').write_text(json.dumps(dict(id='example')), encoding='utf-8')
    store.put('analysis', 'example', dict(id='example', frames=[dict(id='a'), dict(id='b')]))
    with TestClient(app) as client:
        assert client.get('/api/examples').json() == []
        folder = tmp_path/'analyses'/'example'
        folder.mkdir(parents=True)
        for id in ('a','b'):
            (folder/f'{id}.png').write_bytes(b'unit-test-file')
        assert client.get('/api/examples').json() == [dict(id='example', label='Pole Barnard’s Star', frames=2)]
