"""Controlled synthetic arrays test algorithms, not claimed NASA detections."""
import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time
from astropy.wcs import WCS
from fastapi.testclient import TestClient

from backend import store
from backend import catalogs
from backend.main import app
from backend.measurements import aperture, recommend
from backend.orientation import direction, footprint
from backend.science import output_wcs
from backend.temporal import combine, product


@pytest.mark.parametrize('ra,dec', [(359.999, 0), (.001, 89.99), (40, -89.99)])
def test_footprint_edges_roundtrip_across_zero_and_poles(ra, dec):
    w = output_wcs(ra, dec, 12, 120)
    polygon = footprint(w, 120)
    points = SkyCoord(np.array(polygon)[:, 0], np.array(polygon)[:, 1], unit='deg')
    x, y = w.world_to_pixel(points)
    assert np.isfinite(polygon).all()
    assert np.all(np.isclose(x, -.5, atol=1e-5) | np.isclose(x, 119.5, atol=1e-5) |
                  np.isclose(y, -.5, atol=1e-5) | np.isclose(y, 119.5, atol=1e-5))


def test_altitude_matches_independent_spherical_formula_two_locations():
    # ICRS-to-apparent corrections < 0.5 deg for this field. The reference is
    # spherical astronomy, not a second invocation of the implementation.
    time = Time('2025-06-01T00:00:00')
    for lat, lon in [(52, 21), (-33, 151)]:
        hour = (time.sidereal_time('apparent', longitude=lon*u.deg).deg-42)*np.pi/180
        expected = np.arcsin(np.sin(np.deg2rad(lat))*np.sin(np.deg2rad(12))+
                             np.cos(np.deg2rad(lat))*np.cos(np.deg2rad(12))*np.cos(hour))*180/np.pi
        result = direction(42, 12, lat, lon, utc=time.isot)
        assert result['altitude_deg'] == pytest.approx(expected, abs=.5)
        assert result['above_horizon'] == (expected >= 0)
        assert not result['refraction']


@pytest.mark.parametrize('alt', [90, -30, 35])
def test_zenith_and_horizon_status(alt):
    time = Time('2025-06-01T00:00:00')
    site = EarthLocation.from_geodetic(21*u.deg, 52*u.deg)
    sky = SkyCoord(az=80*u.deg, alt=alt*u.deg, frame=AltAz(obstime=time, location=site, pressure=0*u.hPa)).icrs
    result = direction(sky.ra.deg, sky.dec.deg, 52, 21, utc=time.isot)
    assert result['altitude_deg'] == pytest.approx(alt, abs=1e-6)
    assert (result['azimuth_deg'] is None) == (alt == 90)
    assert result['above_horizon'] == (alt >= 0)


def test_native_aperture_recovers_injected_flux_and_linear_variance():
    y, x = np.indices((51, 51))
    distance = np.hypot(x-25, y-25)
    source = distance <= 4
    data = np.full((51, 51), 100.)
    data[source] += 7
    variance = np.full_like(data, 4)
    flags = np.zeros(data.shape, dtype=np.uint32)
    r = aperture(data, variance, flags, 1, distance, 4)
    assert r['aperture_sum'] == pytest.approx(source.sum()*7)
    assert r['random_error']**2 == pytest.approx(4*source.sum()+source.sum()**2*4/r['background_pixels'])
    flags[25, 25] = 1
    with pytest.raises(ValueError):
        aperture(data, variance, flags, 1, distance, 4)


def test_neighbor_diagnostic_does_not_claim_isolation():
    y, x = np.indices((51, 51))
    distance = np.hypot(x-25, y-25)
    data = np.zeros((51, 51)); data[25, 35] = 50
    result = aperture(data, np.ones_like(data), np.zeros(data.shape, np.uint32), 1, distance, 4)
    assert result['neighbor_warning']


def test_stack_preserves_fixed_weights_and_masks_missing_or_mismatched_pixels():
    a = np.array([[2., np.nan, 2.]])
    b = np.array([[6., 6., 6.]])
    wl = [np.array([[1., 1., 1.]]), np.array([[1.001, 1.001, 2.]])]
    bw = [np.full((1, 3), .04)]*2
    out = combine([a, b], wl, bw, [1, 3], 'stack')
    assert out[0, 0] == pytest.approx(5)
    assert np.isnan(out[0, 1:]).all()


def test_difference_preserves_sign():
    a, b = np.array([[3., 1.]]), np.array([[1., 4.]])
    assert combine([a, b], [np.ones((1, 2))]*2, [np.ones((1, 2))]*2, [1, 1], 'difference').tolist() == [[2, -3]]


def test_long_stack_and_duplicate_exposures_rejected():
    manifest = dict(id='test', frames=[dict(id='a', mjd=1, unit='MJy/sr'), dict(id='b', mjd=3, unit='MJy/sr')])
    with pytest.raises(ValueError, match='okno'):
        product(manifest, ['a', 'b'], [1, 1], 'stack', 24)
    with pytest.raises(ValueError, match='różne'):
        product(manifest, ['a', 'a'], [1, 1], 'stack', 24)


def test_recommendation_never_invents_weights_without_validation():
    r = recommend(dict(rows=[]))
    assert r['weights'] is None
    assert r['status'] == 'insufficient_validation'


def test_gaia_propagates_motion_and_preserves_missing_motion_epoch(tmp_path, monkeypatch):
    from astropy.table import Table, MaskedColumn
    monkeypatch.setattr(store, 'ROOT', tmp_path)
    table = Table(dict(Source=[1, 2], RA_ICRS=[359.999, 10.], DE_ICRS=[0., 20.],
                       pmRA=MaskedColumn([1000., 0.], mask=[False, True]), pmDE=[0., 0.]))
    calls = []
    class Client:
        def __init__(self, **kwargs):
            calls.append(kwargs['vizier_server'])
        def query_region(self, *args, **kwargs):
            return [table]
    monkeypatch.setattr(catalogs, 'Vizier', Client)
    result = catalogs.gaia(0, 0, 2, Time(2026, format='jyear').mjd)
    assert result['sources'][0]['ra'] == pytest.approx(.00177778, abs=1e-6)
    assert result['sources'][0]['propagated']
    assert not result['sources'][1]['propagated']
    assert result['sources'][1]['ra'] == 10
    assert catalogs.gaia(0, 0, 2, Time(2026, format='jyear').mjd) == result
    assert len(calls) == 1  # cached catalog; no network request on replay


def test_gaia_uses_documented_mirror_after_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'ROOT', tmp_path)
    class Client:
        def __init__(self, **kwargs): self.server = kwargs['vizier_server']
        def query_region(self, *args, **kwargs):
            if self.server == 'vizier.cfa.harvard.edu': raise TimeoutError()
            return []
    monkeypatch.setattr(catalogs, 'Vizier', Client)
    result = catalogs.gaia(0, 0, 2, 61000)
    assert result['service'] == 'vizier.idia.ac.za'
    assert result['sources'] == []


def test_new_api_validation_and_no_location_required_for_field(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'ROOT', tmp_path)
    with TestClient(app) as client:
        r = client.post('/api/field', json=dict(ra='23:59:59', dec='+89:59:00', fov_arcmin=12))
        assert r.status_code == 200 and len(r.json()['footprint']) == 68
        assert client.post('/api/orientation', json=dict(ra=42, dec=12, latitude=100, longitude=0)).status_code == 422
        assert client.post('/api/orientation', json=dict(ra=42, dec=12, latitude=52, longitude=21, utc='invalid')).status_code == 422
