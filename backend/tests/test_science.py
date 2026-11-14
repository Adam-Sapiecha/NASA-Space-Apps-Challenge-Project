import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from reproject import reproject_interp

from backend.archive import coordinates, safe_archive_url
from backend.science import output_wcs, stretch_rgba

@pytest.mark.parametrize("ra,dec", [("nan","0"),("-1","0"),("360","0"),("2","91"),("text","0")])
def test_invalid_coordinates_are_rejected(ra, dec):
    with pytest.raises(ValueError):
        coordinates(ra, dec)

def test_challenge_coordinates_parse_as_hourangle():
    c = coordinates("08:55:10.831", "-07:14:42.53")
    assert c.ra.deg == pytest.approx(133.795129167, abs=1e-8)
    assert c.dec.deg == pytest.approx(-7.245147222, abs=1e-8)

def test_wcs_crosses_ra_zero_and_preserves_north_up():
    w = output_wcs(359.999, 30, 12, 120)
    c = SkyCoord([359.999, .001], [30, 30.001], unit="deg")
    x, y = w.world_to_pixel(c)
    restored = w.pixel_to_world(x, y)
    assert np.max(restored.separation(c).arcsec) < 1e-5
    assert y[1] > y[0]
    assert x[1] < x[0]

def test_reprojection_preserves_stationary_source_position():
    a = output_wcs(42, 12, 12, 120)
    b = output_wcs(42, 12, 12, 120)
    b.wcs.crpix += [4, -3]
    yy, xx = np.indices((120,120))
    source = np.exp(-((xx-64)**2+(yy-57)**2)/8)
    shifted, _ = reproject_interp((source,b), a, shape_out=(120,120))
    # Source sky position in B must land at the same celestial location in A.
    expected = a.world_to_pixel(b.pixel_to_world(64,57))
    actual = np.unravel_index(np.nanargmax(shifted), shifted.shape)
    assert actual[1] == pytest.approx(expected[0], abs=.1)
    assert actual[0] == pytest.approx(expected[1], abs=.1)

def test_missing_coverage_is_transparent_not_zero_flux():
    rgba = stretch_rgba(np.array([[np.nan,0.,1.]]),0,1)
    assert rgba[0,:,3].tolist() == [0,255,255]
    assert rgba[0,1,0] == 0
    assert rgba[0,2,0] == 255

@pytest.mark.parametrize("url", ["http://irsa.ipac.caltech.edu/ibe/data/spherex/a", "https://evil.example/a", "https://irsa.ipac.caltech.edu.evil.example/ibe/data/spherex/a", "https://irsa.ipac.caltech.edu/other/a"])
def test_downloads_are_restricted_to_archive_products(url):
    with pytest.raises(ValueError):
        safe_archive_url(url)
