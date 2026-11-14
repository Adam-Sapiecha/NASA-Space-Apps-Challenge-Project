import json

import numpy as np
import pytest
from astropy.io import fits
from fastapi.testclient import TestClient

from backend import science, store
from backend.main import app
from backend.measurements import measure


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'ROOT', tmp_path)
    monkeypatch.setattr(science, 'ROOT', tmp_path)


def test_note_round_trip_validates_frames_and_preserves_view():
    store.put('analysis', 'analysis', dict(frames=[dict(id='a', mjd=1), dict(id='b', mjd=2), dict(id='c', mjd=3)]))
    body = dict(kind='motion', text='Hipoteza użytkownika', frame_ids=['a', 'b'], point=dict(x=.2, y=.3),
                anchors=[dict(x=.2, y=.3, frameId='a', mjd=1), dict(x=.4, y=.5, frameId='b', mjd=2)],
                route_checks={'c': 'unknown'}, mode='route', series_only=False)
    with TestClient(app) as client:
        response = client.post('/api/analyses/analysis/notes', json=body)
        assert response.status_code == 201
        saved = response.json()
        assert client.get('/api/notes/' + saved['id']).json() == saved
        assert saved['route_checks'] == {'c': 'unknown'}
        assert saved['series_only'] is False
        assert saved['text'] == body['text']
        for bad in [dict(frame_ids=['a', 'foreign']), dict(point=dict(x=2, y=0)),
                    dict(anchors=[dict(x=.2, y=.3, frameId='a', mjd=99)]),
                    dict(route_checks={'a': 'fits'}), dict(text='x'*3001)]:
            assert client.post('/api/analyses/analysis/notes', json={**body, **bad}).status_code == 422


def test_note_links_only_measurement_of_its_own_point():
    store.put('analysis', 'analysis', dict(frames=[dict(id='a', mjd=1), dict(id='b', mjd=2)]))
    store.put('measurement', 'measurement', dict(analysis_id='analysis', point=dict(x=.2, y=.3)))
    body = dict(frame_ids=['a', 'b'], point=dict(x=.2, y=.3), measurement_id='measurement')
    with TestClient(app) as client:
        response = client.post('/api/analyses/analysis/notes', json=body)
        assert response.status_code == 201
        assert response.json()['measurement_id'] == 'measurement'
        body['point'] = dict(x=.4, y=.5)
        assert client.post('/api/analyses/analysis/notes', json=body).status_code == 422


def test_legacy_cached_measurement_restores_point_without_remeasurement(monkeypatch):
    cached = dict(id='measurement', analysis_id='analysis', rows=[dict(flux_mjy=1)])
    writes = []
    monkeypatch.setattr(store, 'get', lambda kind, key: cached)
    monkeypatch.setattr(store, 'put', lambda kind, key, value: writes.append(value))
    result = measure(dict(id='analysis'), .2, .3, 12.4)
    assert result['point'] == dict(x=.2, y=.3)
    assert result['rows'] == [dict(flux_mjy=1)]
    assert len(writes) == 1


def test_partial_analysis_keeps_one_frame_and_retry_reuses_it(tmp_path, monkeypatch):
    observations = [dict(id='a'*20, mjd=1, date='2026-01-01T00:00:00', band='D1'),
                    dict(id='b'*20, mjd=2, date='2026-01-02T00:00:00', band='D1')]
    source = dict(id='search', ra=42, dec=0, fov_arcmin=2, observations=observations)
    calls = []
    native = tmp_path/'native.fits'
    native.write_bytes(b'controlled fixture, not archive data')

    def download(obs, *args):
        calls.append(obs['id'])
        if obs['id'].startswith('b') and calls.count(obs['id']) == 1:
            raise TimeoutError('controlled failure')
        return native

    def read_frame(path, coord, wcs, pixels):
        image = np.arange(pixels*pixels, dtype=float).reshape(pixels, pixels)
        return image, np.zeros_like(image, dtype=np.uint32), image*0+1, image*0+.04, dict(
            unit='MJy/sr', wavelength_um=1., bandwidth_um=.04, coverage=1., flag_definitions={}, masked_flags=[])

    monkeypatch.setattr(science, 'download', download)
    monkeypatch.setattr(science, 'read_frame', read_frame)
    science.build_analysis('partial', source, [o['id'] for o in observations])
    partial = store.get('analysis', 'partial')
    assert store.get('job', 'partial')['status'] == 'complete'
    assert len(partial['frames']) == 1
    assert len(partial['failures']) == 1
    science.build_analysis('retry', source, [o['id'] for o in observations], partial)
    retried = store.get('analysis', 'retry')
    assert len(retried['frames']) == 2
    assert retried['failures'] == []
    assert calls.count('a'*20) == 1
    assert calls.count('b'*20) == 2
    assert fits.getdata(tmp_path/'analyses'/'retry'/('a'*20+'.fits')).shape == (32, 32)
    assert json.loads((tmp_path/'analyses'/'partial'/'manifest.json').read_text())['failures']


def test_retry_cannot_reuse_frames_from_a_different_search():
    store.put('search', 'new', dict(id='new', observations=[dict(id='a'), dict(id='b')]))
    store.put('analysis', 'old', dict(search=dict(id='other'), frames=[dict(id='a')], failures=[dict(observation='b')]))
    with TestClient(app) as client:
        response = client.post('/api/analyses', json=dict(search_id='new', observation_ids=['a', 'b'], retry_of='old'))
        assert response.status_code == 422
