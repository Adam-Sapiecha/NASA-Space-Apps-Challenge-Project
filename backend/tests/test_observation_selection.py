"""Selection gates use controlled images; these tests do not claim detections."""
import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from fastapi.testclient import TestClient

from backend import main, science, store, observation_selection as selection


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(store, 'ROOT', tmp_path)
    monkeypatch.setattr(science, 'ROOT', tmp_path)


def obs(id, mjd, band='D1'):
    return dict(id=id, mjd=mjd, band=band, date='2026-01-01T00:00:00',
                url=f'https://irsa.ipac.caltech.edu/ibe/data/spherex/dr1/{id}.fits')


def checked(id, mjd, *, band='D1', wavelength=1., valid=True, central=True):
    return dict(**obs(id, mjd, band), aperture_valid=valid, central_valid=central,
                spectral_valid=True, has_image_data=True, local_coverage=1. if central else 0.,
                wavelength_um=wavelength, bandwidth_um=.04, neighbor_warning=False)


def test_stratification_fills_sparse_time_slots_and_all_detectors():
    rows = [obs(str(i), i*.001) for i in range(20)]+[obs('late', 100)]
    result = selection.spread(rows, 8)
    assert len(result) == 8
    assert result[0]['id'] == '0' and result[-1]['id'] == 'late'
    source = dict(ra=42, dec=0, fov_arcmin=6,
                  observations=[obs(f'{band}-{i}', i, band) for band in ['D1','D2','D3','D4','D5','D6'] for i in range(20)])
    planned = selection.candidate_plan(source, 24)
    assert len(planned) == len({o['id'] for o in planned}) == 24
    assert {o['band'] for o in planned} == {'D1','D2','D3','D4','D5','D6'}
    assert all(sum(o['band'] == band for o in planned) == 4 for band in ['D1','D2','D3','D4','D5','D6'])


def test_valid_local_apertures_beat_long_invalid_baselines_without_using_flux():
    rows = [checked('bad-a', 0, valid=False), checked('bad-b', 1000, valid=False),
            checked('good-a', 400, band='D6', wavelength=4.5), checked('good-b', 410, band='D6', wavelength=4.51)]
    result = selection.choose(rows)
    assert result['pair_ids'] == ['good-a','good-b']
    assert result['status'] == 'aperture_pair_available'
    for r in rows:
        r['flux_mjy'] = 1e20 if not r['aperture_valid'] else -1e20
    assert selection.choose(rows) == result


def test_motion_baseline_beats_small_coverage_differences_in_the_same_quality_tier():
    rows=[checked('early',0),checked('nearby',7),
          dict(checked('late',300),local_coverage=.9,neighbor_warning=True),
          checked('wrong-band',1000,wavelength=2.)]
    result=selection.choose(rows)
    assert result['pair_ids']==['early','late']
    assert result['baseline_days']==300
    assert 'nearby' in result['selected_ids']  # Keep a compatible intermediate epoch.
    assert 'wrong-band' not in result['selected_ids']
    assert result['status']=='aperture_pair_available'


def test_rejects_simultaneous_or_incompatible_local_bands_and_chain():
    assert selection.choose([checked('a', 1), checked('b', 1)])['pair_ids'] == []
    assert selection.choose([checked('a', 1), checked('b', 2, wavelength=2)])['pair_ids'] == []
    rows = [checked('a', 0), checked('b', 2, wavelength=1.015), checked('c', 4, wavelength=1.03)]
    result = selection.choose(rows)
    chosen = [r for r in rows if r['id'] in result['selected_ids']]
    assert len(chosen) == 2
    assert all(selection.compatible(a,b) for i,a in enumerate(chosen) for b in chosen[i+1:])


def test_flagged_source_can_be_viewed_without_becoming_valid_photometry():
    result = selection.choose([checked('a', 0, valid=False, central=False), checked('b', 100, valid=False, central=False)])
    assert result['status'] == 'image_pair_only'
    assert result['selected_ids'] == ['a','b']
    assert 'do not both pass' in result['summary']
    assert selection.choose([dict(checked('a',0), has_image_data=False, central_valid=False)])['selected_ids'] == []


def test_native_flags_and_background_use_photometry_gates(tmp_path, monkeypatch):
    w = science.output_wcs(42, 0, 6, 61)
    header = w.to_header(); header['BUNIT'] = 'MJy/sr'
    image = np.ones((61,61));variance=np.ones_like(image);flags=np.zeros(image.shape,np.uint32)
    flags_header = fits.Header();flags_header['MSKN0']='SUR_ERROR';flags_header['MSKN1']='SOURCE'
    path=tmp_path/'native.fits'
    def write():
        fits.HDUList([fits.PrimaryHDU(),fits.ImageHDU(image,header=header,name='IMAGE'),
                      fits.ImageHDU(variance,name='VARIANCE'),fits.ImageHDU(flags,header=flags_header,name='FLAGS')]).writeto(path,overwrite=True)
    class Spectral:
        def pixel_to_world(self,*args):return 4.5*u.um,.04*u.um
    monkeypatch.setattr(selection,'WCS',lambda h,**kw:Spectral() if kw.get('key') else WCS(h))
    write();coord=SkyCoord(42,0,unit='deg')
    assert selection.native_quality(path,coord,12.4)['aperture_valid']
    flags[30,30]=1
    write();result=selection.native_quality(path,coord,12.4)
    assert not result['aperture_valid'] and not result['central_valid']
    flags[:]=2
    write();result=selection.native_quality(path,coord,12.4)
    assert not result['aperture_valid'] and result['central_valid']
    assert 'tła' in result['reason']


def test_expansion_preserves_output_geometry_and_native_cache_key(tmp_path, monkeypatch):
    source=dict(ra=42,dec=0,fov_arcmin=6)
    calls=[]
    def download(row, center, fov, **kwargs):
        calls.append(row.get('cutout_fov_arcmin',fov))
        return tmp_path/str(calls[-1])
    monkeypatch.setattr(science,'download',download)
    monkeypatch.setattr(selection,'native_quality',lambda path,*args:dict(aperture_valid=path.name=='12',background_clipped=path.name!='12',spectral_valid=True))
    row=selection.inspect_observation(obs('a',61000),source)
    assert calls==[6,12]
    assert source['fov_arcmin']==6 and row['cutout_fov_arcmin']==12
    assert row['aperture_valid']
    center=SkyCoord(42,0,unit='deg')
    assert science.download_path(dict(obs('a',0),cutout_fov_arcmin=12),center,6)==science.download_path(obs('a',0),center,12)


def test_auto_api_bounds_jobs_and_binds_catalogue_to_actual_field(monkeypatch):
    store.put('search','s',dict(id='s',ra=42,dec=0,fov_arcmin=6,observations=[]))
    queued=[]
    monkeypatch.setattr(main,'submit_job',lambda *args:queued.append(args))
    with TestClient(main.app) as client:
        assert client.post('/api/analyses/auto',json=dict(search_id='s',target_id='barnard')).status_code==422
        assert client.post('/api/analyses/auto',json=dict(search_id='s',candidate_limit=100)).status_code==422
        response=client.post('/api/analyses/auto',json=dict(search_id='s',candidate_limit=12))
        assert response.status_code==202
        assert queued[0][1] is selection.build_selected_analysis
        assert store.get('job',response.json()['id'])['phase']=='selection'


def test_parallel_inspection_prepares_only_the_recommended_series(tmp_path, monkeypatch):
    import threading
    observations=[obs(f'{i:020x}',i) for i in range(36)]
    source=dict(id='s',ra=42,dec=0,fov_arcmin=2,observations=observations)
    barrier=threading.Barrier(4)
    lock=threading.Lock()
    active=peak=0
    def inspect(o, *args, **kwargs):
        nonlocal active,peak
        with lock:
            active+=1;peak=max(peak,active)
        barrier.wait(timeout=10)
        with lock:active-=1
        row=checked(o['id'],o['mjd'],wavelength=1. if o['mjd']<2 else 1.+o['mjd']*.3)
        row['cutout_fov_arcmin']=4
        if o['mjd']==35:return dict(row,reason='controlled download failure')
        return dict(row,native_fits_sha256='fixture')
    native=tmp_path/'native.fits';native.write_bytes(b'controlled fixture')
    calls=[]
    def download(o, *args, **kwargs):
        calls.append(o)
        return native
    def read(path, coord, wcs, pixels):
        image=np.arange(pixels*pixels,dtype=float).reshape(pixels,pixels)
        return image,np.zeros_like(image,dtype=np.uint32),image*0+1,image*0+.04,dict(
            unit='MJy/sr',wavelength_um=1.,bandwidth_um=.04,coverage=1.,flag_definitions={},masked_flags=[])
    original=store.put
    progress=[]
    def put(kind, id, value):
        original(kind,id,value)
        if kind=='job' and value.get('phase')=='selection':
            progress.append((value['completed'],value['total']))
    monkeypatch.setattr(selection,'inspect_observation',inspect)
    monkeypatch.setattr(science,'download',download)
    monkeypatch.setattr(science,'read_frame',read)
    monkeypatch.setattr(store,'put',put)
    # science imported put directly; observe both paths without changing storage.
    monkeypatch.setattr(science,'put',put)
    selection.build_selected_analysis('job',source)
    assert peak==4
    assert progress[0]==(0,36) and progress[-1]==(36,36)
    result=store.get('analysis','job')
    assert store.get('job','job')['status']=='complete', store.get('job','job')
    assert not result['provisional']
    assert len(result['frames'])==2
    assert [f['id'] for f in result['frames']]==result['selection']['selected_ids']
    assert set(result['selection']['pair_ids'])==set(result['selection']['selected_ids'])
    assert len(result['selection']['selected_ids'])==2
    assert result['selection']=={k:v for k,v in store.get('selection','job').items() if k!='id'}
    assert result['selection']['complete'] and result['selection']['inspected']==36
    assert any(r.get('reason')=='controlled download failure' for r in result['selection']['candidates'])
    assert not result['failures']
    assert len(calls)==2 and all(o['cutout_fov_arcmin']==4 for o in calls)
    assert result['pixels']==32  # Expanded native cutouts do not enlarge the display field.
    assert all(f['image'].endswith('?v=final') for f in result['frames'])


def test_provisional_images_are_readable_but_measurements_cannot_cache_incomplete_series():
    store.put('analysis','pending',dict(id='pending',provisional=True,frames=[]))
    with TestClient(main.app) as client:
        assert client.get('/api/analyses/pending').status_code==200
        for path,body in [('previews',{}),('measurements',dict(x=.5,y=.5)),('profile',dict(x=.5,y=.5))]:
            response=client.post('/api/analyses/pending/'+path,json=body)
            assert response.status_code==409, (path,response.text)


def test_publishing_retries_a_temporary_windows_file_lock(tmp_path, monkeypatch):
    from pathlib import Path
    temp=tmp_path/'manifest.tmp';temp.write_text('new complete snapshot')
    target=tmp_path/'manifest.json';target.write_text('prior complete snapshot')
    original=Path.replace
    calls=[]
    def replace(path, destination):
        calls.append(path)
        if len(calls)==1:
            assert target.read_text()=='prior complete snapshot'
            raise PermissionError('controlled Windows sharing violation')
        return original(path,destination)
    monkeypatch.setattr(Path,'replace',replace)
    monkeypatch.setattr(science.time,'sleep',lambda seconds:None)
    science.replace_ready_file(temp,target)
    assert len(calls)==2 and target.read_text()=='new complete snapshot'
