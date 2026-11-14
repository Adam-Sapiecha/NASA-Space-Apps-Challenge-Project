import io

import numpy as np
import pytest
from astropy.io import fits
from astropy.table import Table
from fastapi.testclient import TestClient
from scipy.special import erf

from backend import store, irsa_resources, moving_objects
from backend.calibrated import fit_epsf
from backend.main import app
from backend.reference_spectra import read_reference, compare_reference
from backend.source_discovery import extract


@pytest.fixture(autouse=True)
def isolated_store(tmp_path,monkeypatch):
    monkeypatch.setattr(store,'ROOT',tmp_path)


def test_calibration_uses_parent_pixels_and_preserves_outside(tmp_path):
    path=tmp_path/'cal.fits'
    fits.HDUList([fits.PrimaryHDU(),fits.ImageHDU(np.arange(30).reshape(5,6),header=fits.Header({'BUNIT':'um'}),name='CWAVE')]).writeto(path)
    header={'CRPIX1A':-1,'CRPIX2A':0}
    result=irsa_resources.calibration_cutout(path,'CWAVE',header,(3,5))
    np.testing.assert_array_equal(result[:,:4],np.arange(30).reshape(5,6)[1:4,2:6])
    assert np.isnan(result[:,4]).all()
    with pytest.raises(ValueError):
        irsa_resources.calibration_cutout(path,'CWAVE',{'CRPIX1A':.5,'CRPIX2A':0},(2,2))
    with pytest.raises(ValueError):irsa_resources.parent_coordinates({},1,1)


@pytest.mark.parametrize('phase',[(0.,0.),(.37,.21),(-.41,.44)])
def test_epsf_recovers_known_flux_with_subpixel_phase_and_area_gradient(phase):
    # Analytic pixel-convolved Gaussian, independently evaluated on native pixels.
    sigma=.7
    def response(v):return .5*(erf((v+.5)/(np.sqrt(2)*sigma))-erf((v-.5)/(np.sqrt(2)*sigma)))
    grid=(np.arange(33)-16)/5
    epsf=response(grid)[:,None]*response(grid)[None,:]
    yy,xx=np.indices((25,25));x,y=12+phase[0],12+phase[1]
    area=.8+.005*xx
    flux=2.8
    profile=response(yy-y)*response(xx-x)
    data=flux*profile/area+3+.02*(xx-x)-.03*(yy-y)
    fitted=fit_epsf(data,np.full(data.shape,.01),np.ones(data.shape,bool),area,x,y,epsf,5,5)
    assert fitted['flux_mjy']==pytest.approx(flux,rel=.005)
    assert fitted['background']==pytest.approx(3,abs=.002)
    assert fitted['error_mjy']>0
    assert fitted['reduced_chi2']<.001
    with pytest.raises(ValueError):fit_epsf(data,np.ones_like(data),np.zeros_like(data,bool),area,x,y,epsf,5,5)


def test_sep_detects_realistic_source_and_excludes_masked_artifact():
    rng=np.random.default_rng(41);yy,xx=np.indices((96,96))
    data=rng.normal(0,1,(96,96))+35*np.exp(-((xx-35.3)**2+(yy-44.8)**2)/3)
    data[10:14,10:14]=1000
    mask=np.zeros(data.shape,bool);mask[8:16,8:16]=True
    objects,meta=extract(data,np.ones_like(data),mask,5,3)
    assert len(objects)==1
    assert objects[0]['x']==pytest.approx(35.3,abs=.2)
    assert objects[0]['y']==pytest.approx(44.8,abs=.2)
    assert .9<meta['valid_fraction']<1


CSV='wavelength,flux,flux_err,mjd,ra,dec,det_id,data_collection,lvf_id,lambda_width\n1.2,1200,50,60000,10,20,2,spherex_dr1,obs-test,.04\n'


def test_csv_units_and_unique_exposure_match():
    rows,sha=read_reference(CSV,'csv')
    assert rows[0]['flux_mjy']==pytest.approx(1.2)
    assert rows[0]['error_mjy']==pytest.approx(.05)
    assert len(sha)==64
    frame=dict(id='frame',obs_id='obs-test',band='SPHEREx-D2',mjd=60000.,date='2023-02-25T00:00:00')
    manifest=dict(id='analysis',frames=[frame],search=dict(collection='spherex_dr1'))
    local=dict(id='cal',method='release-maps-epsf-2',ra=10,dec=20,rows=[dict(id='frame',valid=True,wavelength_um=1.2,bandwidth_um=.04,epsf=dict(flux_mjy=1.3),aperture_flux_mjy=1.1)])
    result=compare_reference(local,manifest,CSV,'csv')
    assert result['matched_count']==1
    assert result['matches'][0]['difference_mjy']==pytest.approx(.1)
    for bad in [CSV+CSV.splitlines()[1]+'\n',CSV.replace('60000','60001'),CSV.replace('spherex_dr1','spherex_qr3'),CSV.replace(',10,20,',',11,20,')]:
        assert compare_reference(local,manifest,bad,'csv')['matched_count']==0


def test_votable_uses_declared_units():
    table=Table(dict(wavelength=[1200.],flux=[.0012],flux_err=[.00005],mjd=[60000.],ra=[10.],dec=[20.],det_id=[2]))
    table['wavelength'].unit='nm';table['flux'].unit='Jy';table['flux_err'].unit='Jy'
    output=io.BytesIO();table.write(output,format='votable')
    rows,_=read_reference(output.getvalue().decode(),'votable')
    assert rows[0]['wavelength_um']==pytest.approx(1.2)
    assert rows[0]['flux_mjy']==pytest.approx(1.2)


@pytest.mark.parametrize('xml',['<broken','<!DOCTYPE x><x/>','<x><STREAM href="https://example.invalid/data"/></x>'])
def test_invalid_or_external_xml_is_rejected(xml):
    with pytest.raises(ValueError):read_reference(xml,'votable')


def test_hips_layer_properties_and_tile_address(monkeypatch):
    metadata=dict(properties={'dataproduct_type':'cube','hips_cube_depth':'102','data_cube_crval3_arr':'1 2','hips_order':'5'},layers=[dict(available=i not in (50,51),wavelength_um=1+i/100) for i in range(102)])
    monkeypatch.setattr(irsa_resources,'hips_metadata',lambda:metadata)
    properties=irsa_resources.layer_properties(29,'http://testserver')
    assert 'dataproduct_type = image' in properties
    assert 'hips_cube_depth' not in properties
    assert 'hips_service_url = http://testserver/api/irsa/hips/layers/29' in properties
    for index in (-1,50,51,102):
        with pytest.raises(ValueError):irsa_resources.layer_properties(index,'http://testserver')
    class Stream:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def raise_for_status(self):pass
        def iter_bytes(self):yield b'\x89PNGtest'
    urls=[]
    def stream(method,url,**kwargs):urls.append(url);return Stream()
    monkeypatch.setattr(irsa_resources.httpx,'stream',stream)
    irsa_resources.hips_tile.cache_clear()
    irsa_resources.hips_tile(0,0,0,0);irsa_resources.hips_tile(29,0,0,0)
    assert urls[0].endswith('/Npix0/Npix0.png')
    assert urls[1].endswith('/Npix0/Npix0_29.png')
    irsa_resources.hips_allsky.cache_clear()
    irsa_resources.hips_allsky(29)
    assert urls[2].endswith('/Norder3/Allsky_29.png')
    with pytest.raises(ValueError):irsa_resources.hips_allsky(50)
    irsa_resources.hips_allsky.cache_clear()
    with pytest.raises(ValueError):irsa_resources.hips_tile(29,0,0,12)
    irsa_resources.hips_tile.cache_clear()


def test_most_zero_results_and_bounded_dates(monkeypatch):
    captured={}
    class Client:
        def query_object(self,**kwargs):captured.update(kwargs);return None
    monkeypatch.setattr(moving_objects,'MostClass',Client)
    result=moving_objects.search_moving('20000001:NID','2025-08-01','2025-08-03')
    assert result['count']==0 and result['rows']==[]
    assert captured['catalog']=='spherex' and captured['obj_name']=='20000001:NID'
    with pytest.raises(ValueError):moving_objects.search_moving('Ceres','2025-01-01','2025-03-01')


def test_irsa_api_rejects_invalid_inputs_and_cross_analysis_reference():
    store.put('analysis','a',dict(id='a',frames=[dict(id='frame')]))
    store.put('irsa_result','cal',dict(kind='calibrated',analysis_id='other'))
    with TestClient(app) as client:
        assert client.post('/api/irsa/most',json=dict(name='Ceres',start_date='2025-01-01',end_date='2025-03-01')).status_code==422
        assert client.post('/api/analyses/a/discovery',json=dict(frame_id='other')).status_code==422
        assert client.post('/api/analyses/a/calibrated',json=dict(x=.5,y=.5,radius_arcsec=100)).status_code==422
        assert client.post('/api/analyses/a/reference',json=dict(calibrated_id='cal',format='csv',content=CSV)).status_code==422
