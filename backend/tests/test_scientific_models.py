"""Controlled tests for physics, leakage prevention and cross-result bindings."""
import hashlib
import json

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.table import Table
from fastapi.testclient import TestClient

from backend import store
from backend import artifact_model as artifacts
from backend import object_context, trajectory
from backend.main import app
from backend.native_diagnostics import fit_stamp
from backend.spectral_models import interpret, absorption_check, FEATURES, band_samples, average_band, planck_fnu
from backend.exposure_weights import weight_plan


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'ROOT', tmp_path)


def test_native_centroid_recovers_subpixel_source_and_rejects_bad_coverage():
    yy, xx = np.indices((17, 17))
    image = 2+.01*xx+12*np.exp(-((xx-8.3)**2+(yy-7.7)**2)/(2*1.2**2))
    fit = fit_stamp(image, np.full_like(image, .04), np.ones_like(image, bool), 8, 8)
    assert fit['x'] == pytest.approx(8.3, abs=.01)
    assert fit['y'] == pytest.approx(7.7, abs=.01)
    assert fit['snr'] > 20 and fit['random_error_px'] > 0
    assert fit['profile'] == 'gaussian_fallback'
    with pytest.raises(ValueError, match='pokrycia'):
        fit_stamp(image, np.ones_like(image), np.zeros_like(image, bool), 8, 8)


def test_fixed_epsf_centroid_fit():
    yy, xx = np.indices((17, 17))
    epsf = np.exp(-((xx-8)**2+(yy-8)**2)/2.8)
    image = 3+10*epsf
    fit = fit_stamp(image, np.full_like(image, .1), np.ones_like(image, bool), 8, 8, epsf)
    assert fit['x'] == pytest.approx(8, abs=.01)
    assert fit['profile'] == 'release_ePSF'


def observations():
    origin = SkyCoord(359.999*u.deg, 20*u.deg)
    result = []
    for i in range(4):
        coord = origin.spherical_offsets_by(i*3*u.arcsec, i*-2*u.arcsec)
        result.append(dict(ra=float(coord.ra.deg), dec=float(coord.dec.deg), mjd=61000+i, error_arcsec=.2))
    return result


def test_motion_crosses_ra_zero_and_propagates_error():
    result = trajectory.linear_motion(observations(), [61003, 61005])
    assert result['motion_east_arcsec_day'] == pytest.approx(3, abs=.001)
    assert result['motion_north_arcsec_day'] == pytest.approx(-2, abs=.001)
    assert result['predictions'][1]['ra'] < .1
    assert result['predictions'][1]['axis_error_arcsec'] > result['predictions'][0]['axis_error_arcsec']
    assert max(result['held_out_errors_arcsec']) < .01
    with pytest.raises(ValueError, match='bazę'):
        trajectory.linear_motion(observations(), [61020])
    with pytest.raises(ValueError, match='trzy'):
        trajectory.linear_motion(observations()[:2], [61003])


def test_gaia_uses_reference_position_and_never_invents_uncertainty():
    candidate = dict(id='star', reference_ra=20., reference_dec=10., pmra=1000., pmdec=0., reference_epoch=2016.)
    result = trajectory.star_positions(candidate, [61000, 62000])
    assert result['predictions'][1]['ra'] > result['predictions'][0]['ra']
    assert result['predictions'][0]['axis_error_arcsec'] is None
    with pytest.raises(ValueError):
        trajectory.star_positions(dict(candidate, pmra=None), [61000])


def test_horizons_preserves_observer_and_missing_errors(monkeypatch):
    seen = {}
    class Client:
        def __init__(self, **kwargs): seen.update(kwargs)
        def ephemerides(self, **kwargs):
            return Table(dict(datetime_jd=[2461000.5], RA=[12.], DEC=[3.], targetname=['Ceres']))
    monkeypatch.setattr(trajectory, 'Horizons', Client)
    result = trajectory.ephemeris('1', [61000], '500@399')
    assert seen['location'] == '500@399' and seen['epochs'] == [2461000.5]
    assert result['predictions'][0]['ra_3sigma_arcsec'] is None


def calibrated_spectrum():
    rows = [dict(id=str(i), valid=True, mjd=61000+i*.0001, wavelength_um=w, bandwidth_um=.03)
            for i, w in enumerate([1., 1.5, 2., 2.5, 3.5, 4.5])]
    values = average_band(planck_fnu(band_samples(rows), 3000), band_samples(rows))*5
    for row, flux in zip(rows, values):
        row['epsf'] = dict(flux_mjy=float(flux), error_mjy=.01)
    return dict(id='cal', method='release-maps-epsf-2', analysis_id='analysis', point=dict(x=.5, y=.5), kind='calibrated', rows=rows)


def test_spectrum_recovers_continuum_without_chemical_claim():
    report = calibrated_spectrum()
    result = interpret(report, [r['id'] for r in report['rows']])
    assert result['models'][0]['temperature_k'] == 3000
    assert result['models'][0]['chi2'] < 1e-10
    assert all(f['status'] == 'insufficient_coverage' for f in result['features'])
    with pytest.raises(ValueError, match='okno'):
        interpret(report, [r['id'] for r in report['rows']], max_hours=.0001)
    bad = dict(name='bad', provenance='test', wavelength_um=[1, 2, 3, 4], relative_fnu=[1, 2, 3, 4])
    with pytest.raises(ValueError, match='pokrywa'):
        interpret(report, [r['id'] for r in report['rows']], templates=[bad])


def test_absorption_requires_continuum_both_sides():
    rows = [dict(wavelength_um=w, bandwidth_um=.01, flux=5. if 4.23<w<4.31 else 10., error=.1)
            for w in (4.08, 4.13, 4.25, 4.28, 4.38, 4.43)]
    result = absorption_check(rows, FEATURES[1])
    assert result['status'] == 'depression_candidate'
    assert result['depth'] == pytest.approx(.5)
    assert absorption_check(rows[:4], FEATURES[1])['status'] == 'insufficient_coverage'


def test_catalog_adapter_propagates_simbad_and_retains_physical_types(monkeypatch):
    def tap(service, query):
        assert 'TOP 501' in query
        return [dict(main_id='Known star', otype='Star', sp_type='M5V', ra=10., dec=0., pmra=1000., pmdec=0.)]
    monkeypatch.setattr(object_context, 'tap', tap)
    result = object_context.catalog_candidates('simbad', 10, 0, 60, 61000)
    assert result['candidates'][0]['object_type'] == 'Star'
    assert result['candidates'][0]['spectral_type'] == 'M5V'
    assert result['candidates'][0]['ra'] > 10
    assert result['candidates'][0]['propagated']


def test_simbad_uses_official_mirror_and_preserves_response_hash(monkeypatch):
    import io
    import httpx
    content = io.BytesIO()
    Table(dict(main_id=['Star'], otype=['Star'], sp_type=['M5'], ra=[10.], dec=[0.], pmra=[0.], pmdec=[0.])).write(content, format='votable')
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return httpx.Response(404 if len(calls) == 1 else 200, content=b'not found' if len(calls) == 1 else content.getvalue(), request=httpx.Request('GET', url))
    monkeypatch.setattr(object_context.httpx, 'get', get)
    result = object_context.catalog_candidates('simbad', 10, 0, 30, 61000)
    assert len(calls) == 2 and result['service_url'] == object_context.SIMBAD_MIRROR
    assert result['response_sha256'] == hashlib.sha256(content.getvalue()).hexdigest()
    assert result['candidates'][0]['object_type'] == 'Star'


def test_allwise_falls_back_to_gator(monkeypatch):
    monkeypatch.setattr(object_context, 'tap', lambda *args: (_ for _ in ()).throw(TimeoutError()))
    monkeypatch.setattr(object_context, 'allwise_gator', lambda *args: [dict(designation='WISE', ra=10., dec=0., w1mpro=11.)])
    result = object_context.catalog_candidates('allwise', 10, 0, 30, 61000)
    assert result['access'] == 'IRSA Gator'
    assert result['candidates'][0]['metadata']['w1mpro'] == 11


def test_weight_plan_checks_every_band_pair_and_quality():
    rows = [dict(id=str(i), valid=True, mjd=61000+i*.001, wavelength_um=w, bandwidth_um=.1,
                 source_sha256=str(i), epsf=dict(error_mjy=float(i+1))) for i, w in enumerate((2., 2.04, 2.08))]
    profile = dict(id='profile', rows=[dict(frame_id=r['id'], valid=True, reduced_chi2=1., bad_fraction=0.) for r in rows])
    report = dict(id='cal', method='release-maps-epsf-2', point=dict(x=.5, y=.5), analysis_id='analysis', rows=rows)
    result = weight_plan(report, profile, '0', 24)
    assert result['frame_ids'] == ['0', '1']
    assert result['weights'] == pytest.approx([.8, .2])
    assert len(result['excluded']) == 1
    profile['rows'][0]['reduced_chi2'] = 5
    assert weight_plan(report, profile, '0', 24)['status'] == 'unavailable'


def test_artifact_model_has_no_synthetic_fallback():
    assert not artifacts.readiness()['ready']
    assert artifacts.train()['status'] == 'insufficient_reviewed_data'
    assert store.get('artifact_active', 'current') is None
    assert artifacts.predict({})['score'] is None


def example(index, analysis=None, sha=None, ra=None):
    return dict(label_id=f'l{index}', source_id=f's{index}', analysis_id=analysis or f'a{index}', frame_id=f'f{index}', y=index%2,
                profile=dict(ra=ra if ra is not None else index*2., dec=0., source_sha256=sha or f'h{index}',method='native-centroid-2',obs_id=f'obs{index}',
                             **{k:float(index%2)*5+.01*index for k in artifacts.FEATURES}))


def test_grouping_prevents_source_exposure_analysis_and_position_leakage():
    data = [example(0, analysis='same'), example(1, analysis='same'), example(2, sha='shared'),
            example(3, sha='shared'), example(4, ra=359.999), example(5, ra=.001)]
    groups = artifacts.connected_groups(data)
    assert groups[0] == groups[1] and groups[2] == groups[3] and groups[4] == groups[5]


def test_artifact_dataset_requires_explicit_review_and_latest_label():
    profile = dict(valid=True, **example(0)['profile'])
    store.put('artifact_features', 's:f', profile)
    label = dict(id='label', source_id='s', frame_id='f', analysis_id='a', label='artifact', created_at='2026-01-01')
    store.put('quality_label', 'label', label)
    assert artifacts.dataset() == []
    store.put('label_review', 'label', dict(reviewer='reviewer'))
    assert len(artifacts.dataset()) == 1
    store.put('quality_label', 'new', dict(label, id='new', label='uncertain', created_at='2026-02-01'))
    assert artifacts.dataset() == []


def test_train_records_disjoint_groups_and_json_model(monkeypatch):
    # Only controlled test data in isolated tmp storage, never a shipped model.
    data = [example(i) for i in range(160)]
    monkeypatch.setattr(artifacts, 'dataset', lambda: data)
    result = artifacts.train()
    assert result['status'] in ('local_holdout_passed', 'experimental_rejected')
    assert result['scientifically_validated'] is False
    assert store.get('artifact_active','current') is None  # insufficient independent test groups for the retention bound
    groups = {name: {g for g, split in zip(result['groups'], result['split']) if split == name} for name in ('train','validation','test')}
    assert not groups['train'] & groups['test'] and not groups['validation'] & groups['test']
    assert len(result['coefficients']) == len(artifacts.FEATURES)+1
    assert store.get('artifact_model', result['id']) == result


def test_api_validates_binding_and_enqueues_exact_settings(monkeypatch):
    import backend.main as main
    store.put('analysis', 'a', dict(id='a', frames=[dict(id=str(i), mjd=61000+i) for i in range(3)]))
    captured = []
    monkeypatch.setattr(main, 'enqueue_irsa', lambda kind, manifest, settings: captured.append((kind, manifest, settings)) or dict(id='job'))
    store.put('irsa_result', 'cal', calibrated_spectrum())
    store.put('irsa_result', 'profile', dict(kind='profile', analysis_id='other', point=dict(x=.5, y=.5)))
    with TestClient(app) as client:
        assert client.post('/api/analyses/a/context', json=dict(x=.5,y=.5,frame_id='foreign')).status_code == 422
        assert client.post('/api/analyses/a/context', json=dict(x=.5,y=.5,frame_id='0')).status_code == 202
        assert captured[-1][0] == 'context'
        assert client.post('/api/ephemerides', json=dict(name='1', dates=['nonsense'])).status_code == 422
        assert client.post('/api/ephemerides', json=dict(name='1', observer='https://bad', dates=['2026-11-14'])).status_code == 422
        assert client.post('/api/ephemerides', json=dict(name='1', dates=['2026-11-14'])).status_code == 202
        assert captured[-1][0] == 'ephemeris'
        assert client.post('/api/irsa/results/cal/weight-plan', json=dict(profile_id='profile',anchor_id='0')).status_code == 422
        assert client.post('/api/irsa/results/profile/stack-weight-plan', json={}).status_code == 422
        assert client.post('/api/artifacts/labels/missing/review', json=dict(reviewer='Test',reason='Test')).status_code == 404
