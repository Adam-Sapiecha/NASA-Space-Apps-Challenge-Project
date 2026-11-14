"""Automatic image-source association and a strictly temporal prediction test.

Known-body ephemerides constrain association, never replace measured positions.
The last exposure is excluded from track selection and fitting.
"""
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

from backend.photometry_math import weighted_fit
from backend.source_discovery import discover

METHOD='automatic-temporal-motion-1'
FLOOR=6.2  # Exploratory one-native-pixel astrometric floor, not calibrated accuracy.
LIMITATIONS=[
    'Short-term apparent linear motion on the sky, not an orbit or a long-term ephemeris.',
    'SEP image centroids can be biased by coma, blends, wavelength and PSF changes.',
    'A one-native-pixel (6.2 arcsec) error floor is exploratory, not an instrument calibration.',
    'Ellipses show formal model uncertainty under independent errors; unmodelled acceleration and systematic errors can exceed them.',
    'One later observation is a temporal check, not an estimated success rate or a discovery claim.',
    'Known-object ephemerides are used only for association. Fitted coordinates come from image pixels.',
]


def motion_previews(manifest):
    """Display-only constant-background removal, never shifting image sources."""
    from astropy.io import fits
    from PIL import Image
    from backend import store
    from backend.science import stretch_rgba
    folder=store.ROOT/'analyses'/manifest['id']
    arrays=[fits.getdata(folder/(f['id']+'.fits')).astype(float) for f in manifest['frames']]
    backgrounds=[float(np.nanmedian(a)) for a in arrays]
    residuals=[a-b for a,b in zip(arrays,backgrounds)]
    values=np.concatenate([a[np.isfinite(a)] for a in residuals]);low,high=map(float,np.percentile(values,[1,99.9]))
    if high<=low:high=low+1
    links={}
    for f,a in zip(manifest['frames'],residuals):
        Image.fromarray(stretch_rgba(a,low,high)[::-1]).save(folder/(f['id']+'.motion.png'))
        links[f['id']]=f"/api/analyses/{manifest['id']}/motion-previews/{f['id']}.png"
    return links,dict(background='Separate constant median per exposure; display only.',background_levels=backgrounds,
        common_limits=[low,high],geometry='Fixed celestial WCS; sources never shifted.')


def coordinate(row):
    return SkyCoord(row['ra'],row['dec'],unit='deg')


def fit_track(rows):
    if len(rows)<3 or len({r['mjd'] for r in rows})<3:
        raise ValueError('At least three independent observation times are required for fitting.')
    times=np.array([r['mjd'] for r in rows],float)
    if not np.isfinite(times).all() or np.ptp(times)<1/1440:
        raise ValueError('The observation baseline is too short.')
    origin=coordinate(rows[0]); coords=SkyCoord([r['ra'] for r in rows],[r['dec'] for r in rows],unit='deg')
    east,north=origin.spherical_offsets_to(coords)
    values=np.column_stack((east.arcsec,north.arcsec))
    errors=np.array([r['error_arcsec'] for r in rows],float)
    if np.max(np.linalg.norm(values,axis=1))>1800:
        raise ValueError('The local model is limited to 30 arcminutes of motion.')
    epoch=float(np.average(times,weights=1/errors**2))
    design=np.column_stack((np.ones(len(times)),times-epoch))
    solutions=[weighted_fit(design,values[:,axis],errors) for axis in range(2)]
    beta=np.column_stack([s[0] for s in solutions])
    residuals=values-design@beta
    chi2=float(np.sum((residuals/errors[:,None])**2)/(2*len(rows)-4))
    inflation=max(1,chi2)
    covariance=solutions[0][1]*inflation
    return dict(origin_ra=float(origin.ra.deg),origin_dec=float(origin.dec.deg),epoch_mjd=epoch,
        coefficients=beta.tolist(),covariance=covariance.tolist(),reduced_chi2=chi2,
        training_start_mjd=float(times.min()),training_end_mjd=float(times.max()),
        baseline_days=float(np.ptp(times)),rms_arcsec=float(np.sqrt(np.mean(np.sum(residuals**2,axis=1)))))


def predict(model,mjd):
    end=model['training_end_mjd']; span=model['baseline_days']
    if not np.isfinite(mjd) or mjd<end-1e-9 or mjd>end+span+1e-9:
        raise ValueError('Forecast is limited to one training baseline beyond the last fitted observation.')
    vector=np.array([1,mjd-model['epoch_mjd']]);offset=vector@np.array(model['coefficients'])
    sky=SkyCoord(model['origin_ra'],model['origin_dec'],unit='deg').spherical_offsets_by(offset[0]*u.arcsec,offset[1]*u.arcsec)
    error=float(np.sqrt(vector@np.array(model['covariance'])@vector))
    return dict(mjd=float(mjd),ra=float(sky.ra.deg),dec=float(sky.dec.deg),axis_error_arcsec=error)


def image_position(manifest,row):
    wcs=WCS(manifest['wcs']);sky=coordinate(row);n=manifest['pixels']
    x,y=wcs.world_to_pixel(sky)
    result=dict(point=dict(x=float((x+.5)/n),y=float(1-(y+.5)/n)),inside=bool(-.5<=x<n-.5 and -.5<=y<n-.5))
    if 'axis_error_arcsec' in row:
        # Numerically transform an angular covariance to the actual image WCS.
        ex,ey=wcs.world_to_pixel(sky.spherical_offsets_by(1*u.arcsec,0*u.arcsec))
        nx,ny=wcs.world_to_pixel(sky.spherical_offsets_by(0*u.arcsec,1*u.arcsec))
        jac=np.array([[ex-x,nx-x],[-(ey-y),-(ny-y)]])/n
        cov=jac@jac.T*row['axis_error_arcsec']**2
        vals,vec=np.linalg.eigh(cov);order=np.argsort(vals)[::-1]
        result['ellipse_2sigma']=dict(rx=float(2*np.sqrt(max(0,vals[order[0]]))),
            ry=float(2*np.sqrt(max(0,vals[order[1]]))),angle_deg=float(np.rad2deg(np.arctan2(vec[1,order[0]],vec[0,order[0]]))))
    return result


def associate(candidates,prior,radius=20):
    if not candidates:raise ValueError('No usable source was detected.')
    ref=coordinate(prior)
    nearby=sorted([(float(ref.separation(coordinate(c)).arcsec),c) for c in candidates],key=lambda r:r[0])
    nearby=[row for row in nearby if row[0]<=radius and row[1].get('sep_flags',0)==0]
    if not nearby:raise ValueError('No isolated image source matches the association window.')
    if len(nearby)>1 and nearby[1][0]-nearby[0][0]<FLOOR:
        raise ValueError('Multiple image sources make the association ambiguous.')
    return dict(nearby[0][1],association_offset_arcsec=nearby[0][0])


def unknown_track(groups):
    """Bounded constant-velocity candidate linking using training images only."""
    proposals=[]
    first,second=groups[:2];dt=second['mjd']-first['mjd']
    if dt<1/1440:raise ValueError('The first two visits are too close in time for blind linking.')
    if any(not g['candidates'] for g in groups):raise ValueError('No usable detections in a training exposure.')
    origin=coordinate(first['candidates'][0]);planes=[]
    for group in groups:
        coords=SkyCoord([r['ra'] for r in group['candidates']],[r['dec'] for r in group['candidates']],unit='deg')
        east,north=origin.spherical_offsets_to(coords)
        planes.append(np.column_stack((east.arcsec,north.arcsec)))
    for ia,a in enumerate(first['candidates'][:30]):
        for ib,b in enumerate(second['candidates'][:30]):
            velocity=(planes[1][ib]-planes[0][ia])/dt
            track=[a,b]
            for j,group in enumerate(groups[2:],2):
                offset=velocity*(group['mjd']-first['mjd'])
                if np.linalg.norm(offset)>1800:break
                distances=np.linalg.norm(planes[j]-(planes[0][ia]+offset),axis=1)
                order=np.argsort(distances)
                if distances[order[0]]>2*FLOOR or (len(order)>1 and distances[order[1]]-distances[order[0]]<FLOOR):break
                track.append(group['candidates'][int(order[0])])
            if len(track)!=len(groups):continue
            rows=[dict(c,mjd=g['mjd'],frame_id=g['frame_id'],error_arcsec=FLOOR) for c,g in zip(track,groups)]
            if coordinate(rows[0]).separation(coordinate(rows[-1])).arcsec<3*FLOOR:continue
            try:model=fit_track(rows)
            except ValueError:continue
            if model['reduced_chi2']<=3:proposals.append((model['rms_arcsec'],rows))
    proposals.sort(key=lambda x:x[0])
    if not proposals:raise ValueError('No unambiguous moving track was found in the training observations.')
    if len(proposals)>1:raise ValueError('Several plausible moving tracks were found; automatic selection is withheld.')
    return proposals[0][1]


def automatic_prediction(manifest,progress=lambda i,n:None):
    result=dict(kind='auto_prediction',method=METHOD,status='unavailable',analysis_id=manifest['id'],
        limitations=LIMITATIONS,frames=[],measurements=[])
    frames=sorted(manifest['frames'],key=lambda f:f['mjd'])
    # Simultaneous channels are not independent times. Prefer the most covered
    # image for duplicate timestamps and sample larger galleries automatically.
    unique={}
    for frame in frames:
        if frame['mjd'] not in unique or frame.get('coverage',0)>unique[frame['mjd']].get('coverage',0):
            unique[frame['mjd']]=frame
    frames=sorted(unique.values(),key=lambda f:f['mjd'])
    if len(frames)>12:
        frames=[frames[int(i)] for i in np.unique(np.rint(np.linspace(0,len(frames)-1,12)).astype(int))]
    result['automatic_selection']=dict(available=len(manifest['frames']),selected=len(frames),method='unique-time-then-time-spaced-maximum-12')
    if len(frames)<4:
        return dict(result,reason='At least four distinct observation times are required: three for fitting and one later test.')
    try:
        groups=[]
        for i,frame in enumerate(frames):
            progress(i,len(frames))
            found=discover(manifest,frame['id'],threshold=5,minarea=3)
            usable=[c for c in found['candidates'] if c['sep_flags']==0]
            groups.append(dict(frame_id=frame['id'],mjd=frame['mjd'],candidates=usable))
        target=manifest.get('motion_target')
        training=groups[:-1]  # Final exposure never participates in track selection.
        if target:
            lookup={r['frame_id']:r for r in target['positions']}
            measured=[dict(associate(g['candidates'],lookup[g['frame_id']]),mjd=g['mjd'],frame_id=g['frame_id'],error_arcsec=FLOOR) for g in training]
            association='known-object-ephemeris-gated-image-centroids'
        else:
            measured=unknown_track(training)
            association='blind-constant-velocity-training-track'
        model=fit_track(measured)
        if model['reduced_chi2']>3:raise ValueError('Image centroids are inconsistent with a constant-velocity model.')
        if coordinate(measured[0]).separation(coordinate(measured[-1])).arcsec<3*FLOOR:
            raise ValueError('Motion is too small relative to the adopted astrometric floor.')
        test=groups[-1];prediction=predict(model,test['mjd'])
        # Measurement is independent of the prediction for a known target.
        prior=lookup[test['frame_id']] if target else prediction
        observed=dict(associate(test['candidates'],prior),mjd=test['mjd'],frame_id=test['frame_id'],error_arcsec=FLOOR)
        error=float(coordinate(prediction).separation(coordinate(observed)).arcsec)
        gate=float(3*np.hypot(prediction['axis_error_arcsec'],FLOOR))
        valid=error<=gate
        forecast=[dict(p,**image_position(manifest,p)) for p in
                  [predict(model,float(t)) for t in np.linspace(model['training_end_mjd'],model['training_end_mjd']+model['baseline_days'],61)]]
        validation=dict(frame_id=test['frame_id'],prediction=dict(prediction,**image_position(manifest,prediction)),
            observed=dict(observed,**image_position(manifest,observed)),error_arcsec=error,
            error_pixels=error/(manifest['search']['fov_arcmin']*60/manifest['pixels']),gate_arcsec=gate,passed=valid,
            held_out=True,selection_used_holdout=False)
        future_model=fit_track(measured+[observed]) if valid else None
        future_forecast=[]
        if future_model and future_model['reduced_chi2']<=3:
            for t in np.linspace(future_model['training_end_mjd'],future_model['training_end_mjd']+future_model['baseline_days'],61):
                p=predict(future_model,float(t))
                future_forecast.append(dict(p,**image_position(manifest,p)))
        return dict(result,status='ready' if valid else 'validation_failed',object=target['name'] if target else 'Automatic moving track',
            association=association,model=model,measurements=[dict(r,**image_position(manifest,r)) for r in measured],
            validation=validation,forecast=forecast if valid else [],future_model=future_model,future_forecast=future_forecast,
            frames=[dict(id=f['id'],mjd=f['mjd'],date=f['date'],image=f['image']) for f in frames],
            background_frame_id=frames[-2]['id'],training_frame_ids=[f['id'] for f in frames[:-1]],held_out_frame_id=frames[-1]['id'])
    except (ValueError,KeyError,OSError) as exc:
        return dict(result,reason=str(exc))
