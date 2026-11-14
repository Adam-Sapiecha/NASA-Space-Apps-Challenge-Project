"""Scientific regression checks on the portable, real-image motion example."""
import hashlib
import json
from pathlib import Path

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from PIL import Image

FOLDER = Path(__file__).resolve().parents[2]/'frontend/public/motion-demo'


def report():
    return json.loads((FOLDER/'evidence.json').read_text())


def test_distinct_real_exposures_keep_one_sky_grid_and_recorded_provenance():
    r = report()
    most_path=FOLDER/'most-response.json'
    assert hashlib.sha256(most_path.read_bytes()).hexdigest()==r['evidence']['source_file_sha256']
    most=json.loads(most_path.read_text())
    headers = []
    assert r['frames'][0]['id'] != r['frames'][1]['id']
    assert 97 < r['minutes'] < 99
    for i,f in enumerate(r['frames']):
        p = FOLDER/f'{i+1}.fits'
        assert hashlib.sha256(p.read_bytes()).hexdigest() == f['displayed_fits_sha256']
        assert f['archive_url'].startswith('https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/')
        observation=next(row for row in most['rows'] if f['archive_url'].endswith(row['uri']))
        a,h = fits.getdata(p, header=True)
        assert a.shape == (117,117)
        headers.append(WCS(h).to_header())
        e=r['evidence']['evidence'][i]
        assert (e['prediction_ra'],e['prediction_dec'])==(observation['ra_obj'],observation['dec_obj'])
        x,y=WCS(h).world_to_pixel(SkyCoord(e['prediction_ra'],e['prediction_dec'],unit='deg'))
        assert np.allclose([(x+.5)/117,1-(y+.5)/117],list(f['point'].values()),atol=1e-8)
    assert headers[0] == headers[1]


def test_visible_target_changes_position_far_more_than_stationary_controls():
    r=report()
    peaks=[]
    for i,e in enumerate(r['evidence']['evidence']):
        a=fits.getdata(FOLDER/f'{i+1}.fits')
        x,y=e['predicted_pixel']; yy,xx=np.indices(a.shape)
        mask=np.hypot(xx-x,yy-y)<=3
        py,px=np.unravel_index(np.nanargmax(np.where(mask,a,np.nan)),a.shape)
        assert np.hypot(px-x,py-y)<2
        peaks.append([px,py])
        # The display retains the bright feature at its original pixel position.
        display=np.array(Image.open(FOLDER/f'{i+1}.png'))
        local=display[116-py-2:116-py+3,px-2:px+3,0]
        assert local.max()>200
    displacement=np.linalg.norm(np.subtract(*peaks))
    assert 45<displacement<49
    # Control maxima must be spatially separated from the comet and remain local.
    assert len(r['stationary_controls'])>=3
    control_offsets=[]
    for c in r['stationary_controls']:
        for p in peaks:
            assert np.linalg.norm(np.subtract(c['a_peak'],p))>8
        control_offsets.append(np.linalg.norm(np.subtract(c['a_peak'],c['b_peak'])))
    assert displacement>10*max(control_offsets)


def test_ephemeris_separation_is_angular_and_not_claimed_as_measured_astrometry():
    r=report()
    e=r['evidence']['evidence']
    a,b=[SkyCoord(x['prediction_ra'],x['prediction_dec'],unit='deg') for x in e]
    assert np.isclose(a.separation(b).arcmin,r['predicted_separation_arcmin'])
    assert 4.7<r['predicted_separation_arcmin']<4.9
    assert any('not precision astrometry' in x for x in r['limitations'])
    assert abs(r['frames'][0]['wavelength_um']-r['frames'][1]['wavelength_um'])>0.1
