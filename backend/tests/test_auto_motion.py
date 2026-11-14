import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits

from backend import auto_motion as auto
from backend.science import output_wcs


def fixture_scene():
    frames=[];sources={};priors=[];origin=SkyCoord(42,0,unit='deg')
    manifest=dict(id='controlled-test-fixture',pixels=117,wcs=dict(output_wcs(42,0,12,117).to_header()),search=dict(fov_arcmin=12))
    for i in range(4):
        coord=origin.spherical_offsets_by(i*50*u.arcsec,i*20*u.arcsec)
        frame=dict(id=str(i),mjd=61000+i*.1,date=f'2025-01-0{i+1}',image=f'/controlled-test-{i}.png')
        row=dict(ra=float(coord.ra.deg),dec=float(coord.dec.deg),id=f'source-{i}',sep_flags=0)
        row.update(auto.image_position(manifest,row))
        frames.append(frame);sources[str(i)]=[row]
        priors.append(dict(frame_id=str(i),ra=row['ra'],dec=row['dec']))
    manifest.update(frames=frames,motion_target=dict(name='Controlled test source',positions=priors))
    return manifest,sources


def install_scene(monkeypatch,sources):
    monkeypatch.setattr(auto,'discover',lambda m,f,**kwargs:dict(candidates=copy.deepcopy(sources[f])))


def test_holdout_cannot_change_fitted_model_or_training_track(monkeypatch):
    m,s=fixture_scene();install_scene(monkeypatch,s)
    first=auto.automatic_prediction(m)
    assert first['status']=='ready'
    assert first['training_frame_ids']==['0','1','2']
    assert first['held_out_frame_id']=='3'
    s['3'][0]['ra']+=.0003
    second=auto.automatic_prediction(m)
    assert second['status']=='ready'
    assert first['model']==second['model']
    assert first['validation']['prediction']==second['validation']['prediction']
    assert second['validation']['error_arcsec']>first['validation']['error_arcsec']
    assert second['validation']['selection_used_holdout'] is False
    assert first['future_model']!=second['future_model']  # Explicitly refitted after validation.


def test_refuses_missing_epochs_and_ambiguous_associations(monkeypatch):
    m,s=fixture_scene();install_scene(monkeypatch,s)
    short=copy.deepcopy(m);short['frames']=short['frames'][:3]
    assert auto.automatic_prediction(short)['status']=='unavailable'
    s['1'].append(dict(s['1'][0],id='confusing-neighbour',ra=s['1'][0]['ra']+.001))
    result=auto.automatic_prediction(m)
    assert result['status']=='unavailable'
    assert 'ambiguous' in result['reason']
    assert 'forecast' not in result


def test_simultaneous_channels_are_not_counted_as_extra_observation_times(monkeypatch):
    m,s=fixture_scene();install_scene(monkeypatch,s)
    m['frames'].append(dict(m['frames'][0],id='simultaneous-other-detector',coverage=-1))
    result=auto.automatic_prediction(m)
    assert result['status']=='ready'
    assert result['automatic_selection']['available']==5
    assert result['automatic_selection']['selected']==4
    assert len(result['measurements'])==3


def test_failed_later_observation_blocks_future_predictions(monkeypatch):
    m,s=fixture_scene()
    s['3'][0]['dec']+=45/3600
    m['motion_target']['positions'][-1]['dec']=s['3'][0]['dec']
    install_scene(monkeypatch,s)
    result=auto.automatic_prediction(m)
    assert result['status']=='validation_failed'
    assert result['validation']['error_arcsec']>result['validation']['gate_arcsec']
    assert result['forecast']==result['future_forecast']==[]


def test_blind_linking_finds_moving_source_without_human_or_catalogue_labels(monkeypatch):
    m,s=fixture_scene();m.pop('motion_target')
    for group in s.values():
        group.append(dict(id='stationary-control',ra=42.05,dec=.05,sep_flags=0))
    install_scene(monkeypatch,s)
    result=auto.automatic_prediction(m)
    assert result['status']=='ready'
    assert result['association']=='blind-constant-velocity-training-track'
    assert result['validation']['error_arcsec']<.1


def test_spherical_fit_crosses_ra_zero_and_limits_extrapolation():
    origin=SkyCoord(359.99,89,unit='deg');rows=[]
    for i in range(3):
        c=origin.spherical_offsets_by(i*30*u.arcsec,i*10*u.arcsec)
        rows.append(dict(ra=float(c.ra.deg),dec=float(c.dec.deg),mjd=61000+i*.1,error_arcsec=6.2))
    model=auto.fit_track(rows)
    near=auto.predict(model,61000.2);far=auto.predict(model,61000.4)
    truth=origin.spherical_offsets_by(120*u.arcsec,40*u.arcsec)
    assert auto.coordinate(far).separation(truth).arcsec<.001
    assert far['axis_error_arcsec']>near['axis_error_arcsec']
    with pytest.raises(ValueError,match='limited'):
        auto.predict(model,61001)


def test_portable_real_data_keep_holdout_separate_and_images_fixed():
    root=Path(__file__).resolve().parents[2]/'frontend/public/prediction-demo'
    r=json.loads((root/'report.json').read_text())
    assert r['status']=='ready' and len(r['measurements'])==3 and len(r['frames'])==4
    assert r['held_out_frame_id'] not in r['training_frame_ids']
    assert r['model']['training_end_mjd']<r['validation']['observed']['mjd']
    error=auto.coordinate(r['validation']['prediction']).separation(auto.coordinate(r['validation']['observed'])).arcsec
    assert error==pytest.approx(r['validation']['error_arcsec'])
    assert error<6.2  # A particular real-image check, not a general success-rate claim.
    headers=[]
    for i,frame in enumerate(r['frames']):
        path=root/f'{i+1}.fits'
        assert hashlib.sha256(path.read_bytes()).hexdigest()==frame['displayed_fits_sha256']
        data,h=fits.getdata(path,header=True);headers.append(h)
        point=(r['measurements'][i] if i<3 else r['validation']['observed'])['point']
        x=int(point['x']*len(data));y=int((1-point['y'])*len(data))
        yy,xx=np.indices(data.shape);d=np.hypot(xx-x,yy-y)
        assert np.nanmax(data[d<3])>np.nanmedian(data[(d>6)&(d<12)])
    for key in ('CRVAL1','CRVAL2','CRPIX1','CRPIX2','CDELT1','CDELT2'):
        assert len({h[key] for h in headers})==1
