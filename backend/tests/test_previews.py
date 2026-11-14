"""Synthetic pixels verify that display modes never rewrite scientific masks."""
import numpy as np
import pytest
from astropy.coordinates import SkyCoord
from astropy.io import fits
from PIL import Image

from backend import science, store
from backend.previews import display_limits, make_previews


@pytest.fixture
def saved_field(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'ROOT', tmp_path)
    monkeypatch.setattr(science, 'ROOT', tmp_path)
    w = science.output_wcs(42, 12, 4, 32)
    folder = tmp_path/'analyses'/'test'
    folder.mkdir(parents=True)
    image = np.ones((32,32)); image[16,16] = 10000
    flags = np.zeros((32,32), np.uint32); flags[16,16] = 1
    masked = image.copy(); masked[16,16] = np.nan
    frames = []
    for id in ('a'*20, 'b'*20):
        frame = dict(id=id, url=f'https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/{id}.fits',
                     flag_definitions={'SUR_ERROR':0})
        native = science.download_path(frame, SkyCoord(42,12,unit='deg'), 4)
        fits.HDUList([fits.PrimaryHDU(), fits.ImageHDU(image, header=w.to_header(),name='IMAGE'),
                      fits.ImageHDU(flags,name='FLAGS')]).writeto(native)
        fits.PrimaryHDU(masked,header=w.to_header()).writeto(folder/f'{id}.fits')
        frames.append(frame)
    return dict(id='test', pixels=32, wcs=dict(w.to_header()), frames=frames,
                search=dict(ra=42, dec=12, fov_arcmin=4))


def test_all_pixels_preview_restores_flagged_pixel_without_changing_science(saved_field):
    manifest = saved_field
    output = make_previews(manifest, 'all', 'full')
    folder = store.ROOT/'previews'/output['id']
    rgba = np.array(Image.open(folder/f"{manifest['frames'][0]['id']}.png"))
    assert rgba[15,16,3] == 255
    assert rgba[15,16,0] == 255  # the bright original pixel is retained
    overlay = np.array(Image.open(folder/f"{manifest['frames'][0]['id']}-quality.png"))
    assert overlay[15*4,16*4,3] > 0
    science_data = fits.getdata(store.ROOT/'analyses'/'test'/f"{manifest['frames'][0]['id']}.fits")
    assert np.isnan(science_data[16,16])
    assert output['display']['common_scale']


def test_quality_filtered_preview_keeps_mask_and_explicitly_reports_mode(saved_field):
    output = make_previews(saved_field, 'valid', 'standard')
    rgba = np.array(Image.open(store.ROOT/'previews'/output['id']/f"{saved_field['frames'][0]['id']}.png"))
    assert rgba[15,16,3] == 0
    assert output['quality'] == 'valid'
    assert output['frames'][0]['display_coverage'] < 1
    assert output['frames'][0]['warned_fraction'] == 0


def test_full_range_uses_extremes_instead_of_percentile_clipping():
    image = np.ones((32,32)); image[0,0] = -100; image[1,1] = 10000
    assert display_limits([image], 'full') == (-100, 10000)
    assert display_limits([image], 'standard')[1] < 10000


def test_previews_are_cached_and_do_not_require_source_again(saved_field):
    first = make_previews(saved_field, 'all')
    second = make_previews(saved_field, 'all')
    assert first == second


def test_independent_display_settings_can_prepare_previews_concurrently(saved_field):
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending=[pool.submit(make_previews,saved_field,'all',mode) for mode in ('faint','full')]
        outputs=[future.result() for future in pending]
    assert outputs[0]['id']!=outputs[1]['id']
    for frame in saved_field['frames']:
        with np.load(store.ROOT/'analyses'/'test'/f"{frame['id']}.display.npz") as data:
            assert data['image'].shape==(32,32)
        for result in outputs:
            Image.open(store.ROOT/'previews'/result['id']/f"{frame['id']}.png").verify()
    assert np.isnan(fits.getdata(store.ROOT/'analyses'/'test'/f"{saved_field['frames'][0]['id']}.fits")[16,16])


def test_pair_display_limits_do_not_depend_on_unrelated_cached_observations(saved_field):
    id=saved_field['frames'][0]['id']
    output=make_previews(saved_field,'all','standard',frame_ids=[id])
    assert output['frame_ids']==[id] and [frame['id'] for frame in output['frames']]==[id]
    assert make_previews(saved_field,'all','standard',frame_ids=[id,id])==output
    with pytest.raises(ValueError):make_previews(saved_field,frame_ids=['foreign'])
