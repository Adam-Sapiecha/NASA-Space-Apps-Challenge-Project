"""Synthetic tests of safeguards, not measured astronomical performance."""
import pytest
from fastapi.testclient import TestClient

from backend import store, source_assessment as assessment
from backend.main import app
from backend.science import output_wcs


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'ROOT', tmp_path)


def manifest():
    return dict(id='analysis', pixels=120, wcs=dict(output_wcs(0, 0, 12, 120).to_header()),
                frames=[dict(id='a', mjd=61000, sha256='abc'), dict(id='b', mjd=61000.01, sha256='def')])


def test_source_is_reproducible_and_not_centroid():
    m = manifest()
    a = assessment.source_record(m, .5, .5)
    assert assessment.source_record(m, .5, .5) == a
    assert assessment.source_record(m, .51, .5)['id'] != a['id']
    assert a['position_error_arcsec'] is None
    assert a['position_method'] == 'user_selected_point'


def test_matching_wraps_ra_and_retains_multiple_candidates():
    cat = dict(sources=[dict(id='1', ra=359.999, dec=0, propagated=True),
                        dict(id='2', ra=.002, dec=0, propagated=False),
                        dict(id='3', ra=2, dec=0, propagated=False)])
    result = assessment.rank_matches(0, 0, cat, 10)
    assert [r['id'] for r in result] == ['1', '2']
    assert result[0]['separation_arcsec'] == pytest.approx(3.6)
    assert result[0]['object_type'] is None


def test_identification_binds_frame_and_saves_report(monkeypatch):
    seen = []
    def gaia(ra, dec, radius, mjd):
        seen.append(mjd)
        return dict(id='cat', sources=[], truncated=True)
    monkeypatch.setattr(assessment.catalogs, 'gaia', gaia)
    result = assessment.identify(manifest(), .5, .5, 'b', 12.4)
    assert seen == [61000.01]
    assert result['status'] == 'no_match' and result['truncated']
    assert store.get('identification', result['id']) == result
    with pytest.raises(ValueError):
        assessment.identify(manifest(), .5, .5, 'foreign', 12.4)


def test_quality_flags_are_not_discovery_labels():
    row = dict(id='a', valid=True, flux_mjy=20., error_mjy=2., flagged=['SOURCE'])
    result = assessment.assess_row(row)
    assert result['status'] == 'review'
    assert 'problemów' not in result['warnings'][0]
    row.update(flagged=['HOT'], neighbor_warning=True, flux_mjy=-1)
    result = assessment.assess_row(row)
    assert result['status'] == 'review' and len(result['warnings']) == 3
    assert assessment.assess_row(dict(row, valid=False))['status'] == 'unusable'
    assert assessment.assess_row(dict(row, error_mjy=float('nan')))['snr'] is None


def calibrated():
    return dict(kind='calibrated', method='release-maps-epsf-2', analysis_id='analysis', rows=[
        dict(id='a', valid=True, mjd=61000., wavelength_um=2., bandwidth_um=.1,
             epsf=dict(flux_mjy=10., error_mjy=1.)),
        dict(id='b', valid=True, mjd=61000.01, wavelength_um=2.01, bandwidth_um=.1,
             epsf=dict(flux_mjy=20., error_mjy=2.))])


def test_inverse_variance_and_guards():
    report = calibrated()
    result = assessment.weighted_flux(report, ['a', 'b'], 24)
    assert result['weights'] == pytest.approx([.8, .2])
    assert result['flux_mjy'] == pytest.approx(12)
    assert result['random_error_mjy'] == pytest.approx(1/(1.25**.5))
    for ids in (['a', 'a'], ['a', 'foreign']):
        with pytest.raises(ValueError):
            assessment.weighted_flux(report, ids, 24)
    with pytest.raises(ValueError, match='okno'):
        assessment.weighted_flux(report, ['a', 'b'], .01)
    report['rows'][1]['wavelength_um'] = 3
    with pytest.raises(ValueError, match='pasma'):
        assessment.weighted_flux(report, ['a', 'b'], 24)
    report = calibrated()
    for row in report['rows']:
        row['source_sha256'] = 'same-fits'
    with pytest.raises(ValueError, match='niezależnym'):
        assessment.weighted_flux(report, ['a', 'b'], 24)
    report = calibrated()
    report['rows'][1]['epsf']['error_mjy'] = 0
    with pytest.raises(ValueError):
        assessment.weighted_flux(report, ['a', 'b'], 24)


def test_api_quality_labels_history_and_foreign_frame(monkeypatch):
    m = manifest()
    store.put('analysis', m['id'], m)
    monkeypatch.setattr(assessment, 'measure', lambda *a: dict(id='measurement', rows=[dict(id='a', valid=False, reason='Brak danych')]))
    with TestClient(app) as client:
        response = client.post('/api/analyses/analysis/quality', json=dict(x=.5, y=.5))
        assert response.status_code == 200
        report = response.json()
        assert report['model'] is None
        path = f"/api/quality/{report['id']}/labels"
        label = dict(frame_id='a', label='uncertain', reason='Brak ważnej obserwacji')
        a = client.post(path, json=label)
        b = client.post(path, json=dict(label, label='artifact'))
        assert a.status_code == b.status_code == 201
        assert a.json()['id'] != b.json()['id']
        assert len(client.get(path).json()) == 2
        assert a.json()['provenance'] == 'unverified_user_assessment'
        assert client.post(path, json=dict(label, frame_id='foreign')).status_code == 422
        assert client.post(path, json=dict(label, reason='   ')).status_code == 422
        assert client.post('/api/analyses/analysis/quality', json=dict(x=2, y=.5)).status_code == 422
        assert client.post('/api/analyses/analysis/identification', json=dict(x=.5, y=.5, frame_id='foreign')).status_code == 422


def test_weighted_flux_api_requires_calibration_and_persists():
    store.put('irsa_result', 'cal', calibrated())
    store.put('irsa_result', 'discovery', dict(kind='discovery'))
    with TestClient(app) as client:
        body = dict(frame_ids=['a', 'b'])
        response = client.post('/api/irsa/results/cal/weighted-flux', json=body)
        assert response.status_code == 200
        result = response.json()
        assert client.get(f"/api/weighted-flux/{result['id']}").json() == result
        assert client.post('/api/irsa/results/discovery/weighted-flux', json=body).status_code == 422
