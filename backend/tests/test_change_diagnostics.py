"""Controlled pairs exercise false-positive safeguards, not discovery claims."""
from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from backend import store
from backend.change_diagnostics import diagnose
from backend.main import app


def measurement():
    base = dict(valid=True, flux_mjy=10., error_mjy=2., wavelength_um=1.2,
                bandwidth_um=.04, flagged=[], neighbor_warning=False,
                background=100., background_scatter=3.)
    return dict(id='measurement', analysis_id='analysis', point=dict(x=.5, y=.5), radius_arcsec=12.4,
                rows=[dict(base, id='a', mjd=60000.), dict(base, id='b', mjd=60100.)])


def check(report, name):
    return next(c for c in report['checks'] if c['name'] == name)


def test_constant_source_with_background_offset_is_not_reported_as_variable():
    m = measurement()
    # Background-subtracted source remains constant despite different raw sky.
    m['rows'][1]['background'] = 300.
    r = diagnose(m, 'a', 'b')
    assert r['metrics']['delta_mjy'] == 0
    assert r['metrics']['random_error_mjy'] == pytest.approx(8**.5)
    assert r['status'] == 'requires_validation'
    assert check(r, 'Tło')['status'] == 'unknown'
    assert check(r, 'PSF i pozycja')['status'] == 'unknown'


def test_injected_change_preserves_sign_without_claiming_detection():
    m = measurement()
    m['rows'][0]['flux_mjy'] = 40.
    r = diagnose(m, 'a', 'b')
    reverse = diagnose(m, 'b', 'a')
    assert r['metrics']['delta_mjy'] == 30
    assert reverse['metrics']['delta_mjy'] == -30
    assert reverse['metrics']['random_error_mjy'] == r['metrics']['random_error_mjy']
    assert r['status'] == 'requires_validation'


@pytest.mark.parametrize('field,value', [('wavelength_um', 1.5), ('mjd', 60000.)])
def test_color_and_simultaneous_exposures_block_variability_interpretation(field, value):
    m = measurement()
    m['rows'][1][field] = value
    assert diagnose(m, 'a', 'b')['status'] == 'blocked'


def test_flags_and_crowding_are_visible_without_automatic_bad_flag_classification():
    m = measurement()
    m['rows'][1].update(flagged=['SOURCE'], neighbor_warning=True)
    before = deepcopy(m)
    r = diagnose(m, 'a', 'b')
    assert check(r, 'Flagi apertury')['status'] == 'caution'
    assert 'SOURCE' in check(r, 'Flagi apertury')['detail']
    assert check(r, 'Otoczenie źródła')['status'] == 'caution'
    assert m == before


def test_legacy_cached_measurement_keeps_sky_position_without_image_point():
    m = measurement()
    del m['point']
    m.update(ra=42., dec=12.)
    r = diagnose(m, 'a', 'b')
    assert r['point'] is None
    assert (r['ra'], r['dec']) == (42., 12.)


@pytest.mark.parametrize('update', [dict(valid=False, reason='Niepełna apertura.'),
                                   dict(flux_mjy=float('nan')), dict(error_mjy=0.), dict(bandwidth_um=-1.)])
def test_unusable_measurements_never_generate_numeric_difference(update):
    m = measurement()
    m['rows'][1].update(update)
    r = diagnose(m, 'a', 'b')
    assert r['status'] == 'blocked'
    assert r['metrics'] is None


def test_api_exports_report_and_rejects_wrong_pair(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'ROOT', tmp_path)
    with TestClient(app) as client:
        store.put('measurement', 'measurement', measurement())
        response = client.get('/api/measurements/measurement/change-diagnostics', params=dict(a='a', b='b'))
        assert response.status_code == 200
        assert response.json()['frame_ids'] == ['a', 'b']
        assert response.json()['measurement_id'] == 'measurement'
        for a, b in [('a', 'a'), ('a', 'foreign')]:
            assert client.get('/api/measurements/measurement/change-diagnostics', params=dict(a=a, b=b)).status_code == 422
        assert client.get('/api/measurements/missing/change-diagnostics', params=dict(a='a', b='b')).status_code == 404
