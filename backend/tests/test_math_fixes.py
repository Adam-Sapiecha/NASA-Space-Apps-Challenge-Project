"""Regression of audited failures; synthetic fixtures are not real detections."""
import numpy as np
import pytest
from astropy import units as u
from astropy.io import fits
from astropy.wcs import WCS
from scipy.special import erf
from fastapi.testclient import TestClient

from backend import store, calibrated, artifact_model
from backend.coordinates import point_sample
from backend.main import app
from backend.science import output_wcs
from backend.evidence import evidence
from backend.measurements import aperture
from backend.irsa_resources import calibration_cutout
from backend.photometry_math import epsf_profile, plane_aperture
from backend.reference_spectra import compare_reference


@pytest.fixture(autouse=True)
def isolated(tmp_path,monkeypatch):
    monkeypatch.setattr(store,'ROOT',tmp_path)


@pytest.mark.parametrize('n',[59,60])
def test_continuous_point_wavelength_and_tan_position_at_noncentral_click(n,tmp_path):
    # Independent TAN direction vector, not a second inverse-WCS call.
    ra,dec=359.999,65.;x,y=.509,.507
    m=dict(id='a',pixels=n,wcs=dict(output_wcs(ra,dec,6,n).to_header()),frames=[dict(id='f',flag_definitions={})])
    folder=tmp_path/'analyses/a';folder.mkdir(parents=True)
    yy,xx=np.indices((n,n));arrays=dict(wavelength=4.+.002*xx+.003*yy,bandwidth=np.full((n,n),.04),valid=np.ones((n,n),bool),flags=np.zeros((n,n),np.uint32))
    np.savez(folder/'f.npz',**arrays);store.put('analysis','a',m)
    with TestClient(app) as client:r=client.get('/api/analyses/a/sample',params=dict(x=x,y=y)).json()
    px,py=x*n-.5,(1-y)*n-.5
    assert r['frames'][0]['wavelength_um']==pytest.approx(4+.002*px+.003*py)
    a,d=np.deg2rad([ra,dec]);origin=np.array([np.cos(d)*np.cos(a),np.cos(d)*np.sin(a),np.sin(d)])
    east=np.array([-np.sin(a),np.cos(a),0]);north=np.array([-np.sin(d)*np.cos(a),-np.sin(d)*np.sin(a),np.cos(d)])
    expected=origin+np.deg2rad(-(px-(n-1)/2)*.1/n)*east+np.deg2rad((py-(n-1)/2)*.1/n)*north
    expected/=np.linalg.norm(expected)
    assert r['ra']==pytest.approx(np.rad2deg(np.arctan2(expected[1],expected[0]))%360,abs=1e-9)
    assert r['dec']==pytest.approx(np.rad2deg(np.arcsin(expected[2])),abs=1e-9)
    arrays['wavelength'][int(py),int(px)]=np.nan
    assert point_sample(m,dict(x=x,y=y),arrays)['wavelength_um'] is None
    assert point_sample(m,dict(x=0,y=0),arrays)['wavelength_um'] is None


def test_route_export_uses_marker_not_unrelated_point_and_does_not_claim_independence(tmp_path):
    n=10;folder=tmp_path/'analyses/a';folder.mkdir(parents=True);yy,xx=np.indices((n,n))
    frames=[dict(id=f'f{i}',date='2026-01-01',mjd=61000+i,flag_definitions={},wavelength_um=99,bandwidth_um=.04) for i in range(2)]
    for f in frames:np.savez(folder/f"{f['id']}.npz",wavelength=xx+2.*yy,bandwidth=np.full((n,n),.04),valid=np.ones((n,n),bool),flags=np.zeros((n,n),np.uint32))
    m=dict(id='a',pixels=n,wcs=dict(output_wcs(42,0,6,n).to_header()),frames=frames,search={},display={})
    anchors=[dict(frameId=f['id'],mjd=f['mjd'],x=x,y=y) for f,x,y in zip(frames,[.6,.4],[.4,.6])]
    note=dict(id='n',frame_ids=['f0','f1'],created_at='2026',kind='uncertain',text='Synthetic',mode='route',point=dict(x=.5,y=.5),anchors=anchors,route_checks={'f0':'uncertain'})
    r=evidence(note,m)
    for a,s in zip(anchors,r['sources']):
        assert s['point']==dict(x=a['x'],y=a['y'])
        assert s['wavelength_um']==pytest.approx((a['x']*n-.5)+2*((1-a['y'])*n-.5))
    assert r['held_out_checks'][0]['independent_epoch'] is None
    note['point']=None
    assert evidence(note,m)['sources'][0]['wavelength_um']==r['sources'][0]['wavelength_um']
    measurement=dict(id='measurement',analysis_id='a',radius_arcsec=12.4,point=dict(x=.3,y=.3),ra=42.,dec=0.,method='synthetic-test',rows=[dict(id=f['id'],valid=False,reason='Synthetic masked point') for f in frames])
    exported=evidence(note,m,measurement)
    assert exported['sky'] is None
    assert exported['measurement_position']['point']==dict(x=.3,y=.3)
    assert exported['sources'][0]['point']==dict(x=.6,y=.4)


def test_variable_area_aperture_and_background_uncertainty_as_linear_contrast():
    yy,xx=np.indices((51,51));d=np.hypot(xx-25,yy-25);a=d<=4;bg=(d>=7.2)&(d<=12)
    k=.7+.003*xx;data=3+.02*xx;data[a]+=2;v=1+.01*yy
    r=aperture(data,v,np.zeros(data.shape,np.uint32),0,d,4,pixel_factor=k)
    weights=np.zeros(data.shape);weights[a]=k[a];weights[bg]=-k[a].sum()/bg.sum()
    assert r['flux_mjy']==pytest.approx(np.sum(weights*data))
    assert r['error_mjy']**2==pytest.approx(np.sum(weights**2*v))
    bg &= xx>25
    plane=plane_aperture(data,v,a,bg,k,25,25)
    assert plane['flux_mjy']==pytest.approx(2*k[a].sum())


def test_calibration_rejects_wrong_hdu_units_detector_and_nontranslation(tmp_path):
    p=tmp_path/'c.fits';h=fits.Header(dict(BUNIT='arcsec2',DETECTOR=6));fits.HDUList([fits.PrimaryHDU(),fits.ImageHDU(np.full((5,5),38.44),header=h,name='IMAGE')]).writeto(p)
    header=dict(CRPIX1A=1,CRPIX2A=1,DETECTOR=6)
    assert calibration_cutout(p,'IMAGE',header,(3,3))[0,0]==38.44
    for changes in [dict(CDELT1A=-1),dict(PC1_2A=.1),dict(CRVAL1A=1),dict(DETECTOR=2),dict(CRPIX1A=-1000.001)]:
        with pytest.raises(ValueError):calibration_cutout(p,'IMAGE',dict(header,**changes),(3,3))
    with pytest.raises(ValueError):calibration_cutout(p,'CWAVE',header,(3,3))
    with fits.open(p,mode='update') as hd:hd['IMAGE'].header['BUNIT']='um'
    with pytest.raises(ValueError):calibration_cutout(p,'IMAGE',header,(3,3))


def test_epsf_phase_normalization_and_crop_are_not_renormalized():
    yy,xx=np.indices((33,33));e=np.exp(-((xx-16)**2+(yy-16)**2)/28.)
    for x in [8,8.2,8.4,8.6,8.8]:
        for y in [8,8.2,8.4,8.6,8.8]:
            assert epsf_profile((17,17),x,y,e,5,5).sum()==pytest.approx(1,abs=1e-12)
    cropped=epsf_profile((17,17),0,0,e,5,5)
    assert 0<cropped.sum()<.8
    with pytest.raises(ValueError):calibrated.fit_epsf(np.ones((17,17)),np.ones((17,17)),np.ones((17,17),bool),np.ones((17,17)),0,0,e,5,5)


def reference_fixture():
    frame=dict(id='f',obs_id='2025W46_1A_0075_4',mjd=61000,date='2026',band='SPHEREx-D6')
    m=dict(id='a',frames=[frame],search=dict(collection='spherex_dr1'))
    local=dict(id='local',method=calibrated.METHOD,ra=20.,dec=0.,rows=[dict(id='f',valid=True,wavelength_um=4.41717,bandwidth_um=.03485,epsf=dict(valid=True,flux_mjy=1.),aperture_flux_mjy=None)])
    csv='wavelength,flux,flux_err,mjd,ra,dec,det_id,data_collection,lvf_id,lambda_width\n4.41717,1000,100,61000,20,0,6,dr1,2025W46_1A_0075_4,.03485\n'
    return m,local,csv


def test_reference_requires_exposure_release_wavelength_and_width():
    m,local,csv=reference_fixture()
    assert compare_reference(local,m,csv,'csv')['matched_count']==1
    for bad in [csv.replace('4.41717,','1.2,'),csv.replace(',dr1,',',,'),csv.replace('2025W46_1A_0075_4','2025W46_1A_0076_4'),csv.replace(',.03485',',.3'),csv.replace(',.03485',','),csv.replace('2025W46_1A_0075_4','2025W46_1A_0075_4D3')]:
        assert compare_reference(local,m,bad,'csv')['matched_count']==0
    with pytest.raises(ValueError):compare_reference(local,m,csv.replace(',6,dr1',',6.9,dr1'),'csv')
    with pytest.raises(ValueError,match='Archiwalna'):compare_reference(dict(local,method='release-maps-epsf-1'),m,csv,'csv')


def test_same_original_exposure_is_one_group_even_for_different_cutouts():
    ex=[dict(analysis_id='a'+str(i),source_id='s'+str(i),profile=dict(ra=20+i,dec=0,source_sha256=str(i),obs_id='same-observation')) for i in range(2)]
    assert len(set(artifact_model.connected_groups(ex)))==1
    assert artifact_model.lower_bound(5,5)==pytest.approx(.05**.2)
    confidence=artifact_model.group_confidence(np.zeros(5,int),np.zeros(5,int),list('abcde'))
    assert confidence['source_retention']['lower_95']<.55


def test_archived_validated_model_is_preserved_but_not_activated():
    store.put('artifact_model','old',dict(method='artifact-logistic-1',status='validated'))
    store.put('artifact_active','current',dict(model_id='old'))
    state=artifact_model.readiness([])
    assert state['active_model'] is None and state['archived_model_ignored']
    assert artifact_model.predict({})['status']=='unavailable'
    assert store.get('artifact_model','old')['status']=='validated'


def test_epsf_is_independent_of_aperture_annulus_gate(tmp_path,monkeypatch):
    n=25;w=output_wcs(42,0,n*6.2/60,n);header=w.to_header();header['BUNIT']='MJy/sr';header['DETECTOR']=6
    yy,xx=np.indices((n,n));response=lambda z:.5*(erf((z+.5)/np.sqrt(2)/.7)-erf((z-.5)/np.sqrt(2)/.7))
    profile=response(xx-12)*response(yy-12);factor=38.44*(u.MJy/u.sr*u.arcsec**2).to(u.mJy);image=8*profile/factor+3
    p=tmp_path/'native.fits';fits.HDUList([fits.PrimaryHDU(),fits.ImageHDU(image,header=header,name='IMAGE'),fits.ImageHDU(np.full((n,n),.0001),name='VARIANCE'),fits.ImageHDU(np.full((n,n),1<<21,np.uint32),name='FLAGS')]).writeto(p)
    m=dict(id='a',pixels=n,wcs=dict(header),search=dict(ra=42,dec=0,fov_arcmin=n*6.2/60,collection='spherex_dr1'),frames=[dict(id='f',obs_id='obs',date='2026',mjd=61000,band='SPHEREx-D6',flag_definitions={'SOURCE':21},sha256='synthetic')])
    monkeypatch.setattr(calibrated,'download_path',lambda *args:p)
    monkeypatch.setattr(calibrated,'calibration_product',lambda *args:(p,dict(sha256='synthetic')))
    monkeypatch.setattr(calibrated,'calibration_cutout',lambda path,ext,h,shape:np.full(shape,38.44 if ext=='IMAGE' else 4.5 if ext=='CWAVE' else .035))
    class Spectral:
        def pixel_to_world(self,*args):return 4.5*u.um,.035*u.um
    monkeypatch.setattr(calibrated,'WCS',lambda h,**kw:Spectral() if kw.get('key')=='W' else WCS(h))
    grid=(np.arange(33)-16)/5;e=response(grid)[:,None]*response(grid)[None,:]
    monkeypatch.setattr(calibrated,'psf_at',lambda *args:(e,dict(oversample_x=5,oversample_y=5)))
    r=calibrated.calibrated_report(m,.5,.5,12.4)['rows'][0]
    assert not r['aperture']['valid'] and r['epsf']['valid'] and r['valid']
    assert r['epsf']['flux_mjy']==pytest.approx(8,rel=.005)
    assert len(r['position_sensitivity'])==4
    # Exercise the complete basic measurement and unit conversion, not only the
    # pure aperture equation. This also rejects accidentally applying 1000x units.
    from backend import measurements
    with fits.open(p,mode='update') as hd:hd['FLAGS'].data[:]=0
    for name in ('download_path','calibration_product','calibration_cutout','WCS'):
        monkeypatch.setattr(measurements,name,getattr(calibrated,name))
    measured=measurements.measure(m,.5,.5,12.4)
    a=(xx-12)**2+(yy-12)**2<=4
    b=((xx-12)**2+(yy-12)**2>=(3.6)**2)&((xx-12)**2+(yy-12)**2<=36)
    expected=8*(profile[a].sum()-a.sum()*profile[b].mean())
    assert measured['rows'][0]['valid']
    assert measured['rows'][0]['flux_mjy']==pytest.approx(expected,rel=.001)
