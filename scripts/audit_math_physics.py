"""Read-only scientific audit. Writes only a new, separate audit directory.

Independent equations are used where possible. Calls to production pure numerical
functions are comparisons, not independent physical validation. No measurement,
download, calibration lookup or writable connection to the application DB is used.
Synthetic controls are explicitly separated from real native FITS measurements.
"""
import csv
import hashlib
import io
import json
import sqlite3
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/audit/math_physics_20261114'
OUT.mkdir(parents=True, exist_ok=True)
sys.path[:0] = [str(ROOT), str(ROOT / '.cache/validation-libs')]
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord, get_body_barycentric
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_area
from scipy.ndimage import map_coordinates
from scipy.special import erf

warnings.filterwarnings('ignore', category=Warning, module='astropy')
DB = sqlite3.connect('file:' + (ROOT/'data/workspace.sqlite').as_posix() + '?mode=ro', uri=True)
def get(kind, id):
    row = DB.execute('SELECT body FROM records WHERE kind=? AND id=?', (kind, id)).fetchone()
    return json.loads(row[0]) if row else None
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def snapshot():
    paths = list((ROOT/'backend').rglob('*.py')) + list((ROOT/'backend').glob('*.json')) + list((ROOT/'frontend/src').rglob('*'))
    return {str(p.relative_to(ROOT)): sha(p) for p in paths if p.is_file()}
def native_path(m, f):
    s=m['search']; params={'center': f"{s['ra']},{s['dec']}d", 'size':str(s['fov_arcmin']/60)}
    key=hashlib.sha256((f['url']+json.dumps(params,sort_keys=True)).encode()).hexdigest()
    return ROOT/'data/fits'/f'{key}.fits'
def calpath(kind, detector):
    p=get('calibration',f'dr1:{kind}:D{detector}')
    return ROOT/'data/calibrations'/(hashlib.sha256(p['url'].encode()).hexdigest()+'.fits')
def vec(ra,dec):
    a,d=np.deg2rad(ra),np.deg2rad(dec)
    return np.stack([np.cos(d)*np.cos(a), np.cos(d)*np.sin(a),np.sin(d)],axis=-1)
def angular(a,b):
    return np.rad2deg(np.arctan2(np.linalg.norm(np.cross(a,b),axis=-1),np.sum(a*b,axis=-1)))*3600
def motion(t, mjd, rv=0):
    """Independent rectilinear 3D propagation in pc and Julian years."""
    a,d=np.deg2rad([t['ra_deg'],t['dec_deg']]); n=vec(t['ra_deg'],t['dec_deg'])
    ea=np.array([-np.sin(a),np.cos(a),0]); ed=np.array([-np.sin(d)*np.cos(a),-np.sin(d)*np.sin(a),np.cos(d)])
    mu=(t['pmra_masyr']*ea+t['pmdec_masyr']*ed)*np.deg2rad(1/3600000)
    distance=1000/t['parallax_mas']; dt=(np.asarray(mjd)-t['epoch_mjd'])/365.25
    v=distance*mu + rv*(365.25*86400/3.085677581491367e13)*n
    r=distance*n+np.atleast_1d(dt)[:,None]*v
    return r/np.linalg.norm(r,axis=1)[:,None]
def map_from_parent(path, name, header, shape):
    yy,xx=np.indices(shape); ix=(xx+1-header['CRPIX1A']).astype(int); iy=(yy+1-header['CRPIX2A']).astype(int)
    with fits.open(path, memmap=False) as hd:
        image=hd[name].data
        good=(ix>=0)&(ix<image.shape[1])&(iy>=0)&(iy<image.shape[0])
        out=np.full(shape,np.nan); out[good]=image[iy[good],ix[good]]
        unit=hd[name].header.get('BUNIT')
    return out,unit
def wcs_area(w,x,y,eps=.01):
    """Local solid angle from Cartesian unit-vector Jacobian, not CD area."""
    def v(x,y):
        a,d=w.all_pix2world(x,y,0); return vec(a,d)
    vx=(v(x+eps,y)-v(x-eps,y))/(2*eps); vy=(v(x,y+eps)-v(x,y-eps))/(2*eps)
    return np.linalg.norm(np.cross(vx,vy),axis=-1)*(180*3600/np.pi)**2
BAD={'OVERFLOW','SUR_ERROR','NONFUNC','MISSING_DATA','HOT','COLD','NONLINEAR','PHANMISS','PERSIST','OUTLIER','CROSSTALK','GHOST','STREAK','BLOOM','SNOWBALL','HALO','SATELLITE_HALO','DICHROIC'}
def aperture_weights(data,var,flags,f,spatial,coord,k,radius=12.4):
    yy,xx=np.indices(data.shape); dd=spatial.pixel_to_world(xx,yy).separation(coord).arcsec
    a=dd<=radius; ann=(dd>=1.8*radius)&(dd<=3*radius)
    mask=sum(1<<b for name,b in f['flag_definitions'].items() if name in BAD)
    sw=sum(1<<b for name,b in f['flag_definitions'].items() if name=='SOURCE')
    valid=np.isfinite(data)&np.isfinite(var)&(var>0)&((flags&mask)==0)
    bg=ann&valid&((flags&sw)==0)
    ret={'aperture_pixels':int(a.sum()), 'annulus_pixels':int(ann.sum()), 'background_pixels':int(bg.sum()),
         'bad_aperture_pixels':int((a&~valid).sum()),'source_in_annulus':int((ann&((flags&sw)!=0)).sum()),
         'aperture_flags':{name:int((a&((flags&(1<<b))!=0)).sum()) for name,b in f['flag_definitions'].items() if np.any(a&((flags&(1<<b))!=0))}}
    sx,sy=spatial.world_to_pixel(coord); scale=np.sqrt(proj_plane_pixel_area(spatial))*3600
    edge=min(sx,sy,data.shape[1]-1-sx,data.shape[0]-1-sy)<3*radius/scale+1
    ret['edge_rejected']=bool(edge)
    ret['valid']=bool(a.sum()>=3 and not np.any(a&~valid) and bg.sum()>=12 and not edge)
    if ret['valid']:
        # An independent linear contrast: disjoint source and background weights.
        weights=np.zeros(data.shape); weights[a]=k[a]; weights[bg]=-np.sum(k[a])/bg.sum()
        ret.update(flux_mjy=float(np.nansum(weights*data)),error_mjy=float(np.sqrt(np.nansum(weights**2*var))),background=float(data[bg].mean()))
    return ret, a,bg,valid
def main():
    before=snapshot()
    (OUT/'production_hashes_before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
    five=json.loads((ROOT/'data/audit/five-targets-final.json').read_text(encoding='utf-8'))
    result={'utc':datetime.now(timezone.utc).isoformat(),'real_targets':[],'real_wise_fixed_point':[], 'synthetic':{},'source_hashes':{},
            'perspective_interpretation':'RV offsets below are sensitivity tests assuming all frozen parameters share their stated reference epoch. For SIMBAD positions transported from Gaia 2016, use the original Gaia-epoch control in recent_extensions.json instead; do not interpret Barnard 0.441 arcsec as the actual production position error.'}
    # New catalogue query, if separately fetched; otherwise explicit missing RV.
    fresh=OUT/'simbad_fresh.csv'; catalog=list(csv.DictReader(io.StringIO(fresh.read_text(encoding='utf-8')))) if fresh.exists() else []
    result['fresh_catalogue']=catalog
    for item in five['targets']:
        t=item['target']; m=get('analysis',item['analysis_id']); tt=np.array([f['mjd'] for f in m['frames']]); pred=motion(t,tt)
        proper=float(angular(pred[0],pred[-1])); dt=tt[-1]-tt[0]
        n=vec(t['ra_deg'],t['dec_deg']); earth=get_body_barycentric('earth',Time(tt,format='mjd')).xyz.to_value(u.au).T
        par=-t['parallax_mas']/1000*(earth-np.sum(earth*n,axis=1)[:,None]*n)
        rvrow=next((row for row in catalog if row.get('main_id')==t['catalogue_id']),None)
        rv=float(rvrow['rvz_radvel']) if rvrow and rvrow.get('rvz_radvel','').strip() else None
        rt={'id':t['id'],'analysis_id':m['id'],'baseline_days':float(dt),'proper_motion_shift_arcsec':proper,'shift_native_6p2_pixels':proper/6.2,
            'earth_parallax_amplitudes_arcsec':np.linalg.norm(par,axis=1).tolist(),'earth_parallax_first_last_change_arcsec':float(np.linalg.norm(par[-1]-par[0])),
            'rv_kms':rv,'perspective_offset_last_arcsec':float(angular(pred[-1],motion(t,tt,rv)[-1])) if rv is not None else None,'frames':[]}
        # Explicit bound using +/-100 km/s when RV has not been established.
        rt['perspective_offset_last_if_rv_100kms_arcsec']=float(angular(pred[-1],motion(t,tt,100)[-1]))
        from backend.targets import position
        astro=np.array([vec(position(t,v)['ra'],position(t,v)['dec']) for v in tt])
        rt['independent_pm_max_difference_arcsec']=float(np.max(angular(pred,astro)))
        skyw=WCS(m['wcs']); screen=np.array([skyw.world_to_pixel(SkyCoord(np.rad2deg(np.arctan2(v[1],v[0]))%360,np.rad2deg(np.arcsin(v[2])),unit='deg')) for v in pred])
        linear=screen[0]+((tt-tt[0])/(tt[-1]-tt[0]))[:,None]*(screen[-1]-screen[0])
        rt['straight_route_max_error_pixels']=float(np.max(np.linalg.norm(screen-linear,axis=1)))
        for f in m['frames']:
            p=native_path(m,f); result['source_hashes'][str(p.relative_to(ROOT))]=sha(p)
            with fits.open(p,memmap=False) as hd:
                h=hd['IMAGE'].header; data=np.array(hd['IMAGE'].data,float); var=np.array(hd['VARIANCE'].data,float); flags=np.array(hd['FLAGS'].data,np.uint32); w=WCS(h)
                coords=position(t,f['mjd']); coord=SkyCoord(coords['ra'],coords['dec'],unit='deg'); sx,sy=map(float,w.world_to_pixel(coord))
                yy,xx=np.indices(data.shape); area=wcs_area(w,xx.astype(float),yy.astype(float))
                const=float(proj_plane_pixel_area(w))*3600**2
                k=np.full(data.shape,const*1e9*(np.pi/(180*3600))**2)
                ap,_,_,_=aperture_weights(data,var,flags,f,w,coord,k)
                sky=w.pixel_to_world(xx,yy); rx,ry=w.world_to_pixel(sky)
                row={'id':f['id'],'date':f['date'],'sha_matches_manifest':sha(p)==f['sha256'],'native_shape':list(data.shape),'predicted_native_xy':[sx,sy],
                    'area_at_prediction_arcsec2':float(wcs_area(w,sx,sy)),'constant_projection_area_arcsec2':const,
                    'area_range_arcsec2':[float(np.min(area)),float(np.max(area))], 'wcs_roundtrip_max_pixels':float(np.max(np.hypot(rx-xx,ry-yy))),
                    'alternate_A':{key:h.get(key) for key in ['CRPIX1A','CRPIX2A','CRVAL1A','CRVAL2A','CDELT1A','CDELT2A','CTYPE1A','CTYPE2A']},
                    'date_obs':h.get('DATE-OBS'),'mjd_obs':h.get('MJD-OBS'),'date_end':h.get('DATE-END'),'mjd_end':h.get('MJD-END'),
                    'pipeline':f.get('processing_version'),'aperture':ap}
                rt['frames'].append(row)
                if t['id']=='wise0855':
                    coord0=skyw.pixel_to_world((m['pixels']-1)/2,(m['pixels']-1)/2); x,y=map(float,w.world_to_pixel(coord0))
                    area_map,unit=map_from_parent(calpath('solid_angle_pixel_map',6),'IMAGE',h,data.shape)
                    wlmap,wlunit=map_from_parent(calpath('spectral_wcs',6),'CWAVE',h,data.shape)
                    bwmap,_=map_from_parent(calpath('spectral_wcs',6),'CBAND',h,data.shape)
                    km=area_map*1e9*(np.pi/(180*3600))**2
                    simple,a,bg,valid=aperture_weights(data,var,flags,f,w,coord0,k)
                    corrected,_,_,_=aperture_weights(data,var,flags,f,w,coord0,km)
                    fr={'id':f['id'],'date':f['date'],'native_xy':[x,y],'solid_angle_map_unit':unit,'wavelength_map_unit':wlunit,
                        'constant_area':simple,'map_area':corrected,'map_area_at_point':float(map_coordinates(area_map,[[y],[x]],order=1)[0]),
                        'jacobian_area_at_point':float(wcs_area(w,x,y)), 'map_over_jacobian_range':[float(np.nanmin(area_map/area)),float(np.nanmax(area_map/area))],
                        'wavelength_cal_um':float(map_coordinates(wlmap,[[y],[x]],order=1)[0]),'bandwidth_cal_um':float(map_coordinates(bwmap,[[y],[x]],order=1)[0])}
                    if simple['valid']:
                        from backend.calibrated import psf_at, fit_epsf
                        epsf,meta=psf_at(hd,x,y); ox=meta['oversample_x'];oy=meta['oversample_y']
                        fit=fit_epsf(data,var,valid,km,x,y,epsf,ox,oy)
                        dx,dy=xx-x,yy-y
                        profile=map_coordinates(epsf,[dy*oy+(epsf.shape[0]-1)/2,dx*ox+(epsf.shape[1]-1)/2],order=3,mode='constant',cval=0)/(epsf.sum()/(ox*oy))
                        g=(dx**2+dy**2<=4.5**2)&valid&(km>0)&np.isfinite(km)
                        X=np.column_stack([profile[g],km[g],km[g]*dx[g],km[g]*dy[g]])/(np.sqrt(var[g])*km[g])[:,None]
                        Q,R=np.linalg.qr(X,mode='reduced'); invr=np.linalg.solve(R,np.eye(4)); cov=invr@invr.T
                        fr['epsf']=dict(fit,zone=meta,condition=float(np.linalg.cond(X)),qr_error_mjy=float(np.sqrt(cov[0,0])),profile_sum=float(profile.sum()),
                                        aperture_profile_fraction=float(profile[a].sum()),nstar=meta['stars'])
                        # Real-data sensitivity to position, not a detection or optimized measurement.
                        shifts=[]
                        for delta in [-.5,0,.5]:
                            r=fit_epsf(data,var,valid,km,x+delta,y,epsf,ox,oy)
                            shifts.append(dict(dx_pixels=delta,flux_mjy=r['flux_mjy'],chi2=r['reduced_chi2']))
                        fr['fixed_position_sensitivity']=shifts
                        if f['id']=='4432acd4afc90868d16b':
                            result['epsf_phase_control']=epsf_phase(epsf,ox,oy)
                            # Actual field: continuous click vs sample-reported pixel centre.
                            nout=m['pixels']; ux,uy=.509,.507
                            c1=skyw.pixel_to_world(ux*nout-.5,(1-uy)*nout-.5)
                            c2=skyw.pixel_to_world(int(ux*nout),nout-1-int(uy*nout))
                            aa=aperture_weights(data,var,flags,f,w,c1,km)[0];bb=aperture_weights(data,var,flags,f,w,c2,km)[0]
                            result['point_convention_control']={'normalized':[ux,uy],'separation_arcsec':float(c1.separation(c2).arcsec),'continuous':aa,'reported_pixel_centre':bb}
                    result['real_wise_fixed_point'].append(fr)
        result['real_targets'].append(rt)
    result['synthetic']=synthetic_controls()
    result['reference_matching_control']=reference_control(get('analysis','4812094a2ce843a8b787837eb13ec845'))
    after=snapshot(); result['production_unchanged']=before==after
    result['production_changed_files']=[k for k in before if before[k]!=after.get(k)]
    result['versions']={name:__import__(name).__version__ for name in ['numpy','scipy','astropy','reproject','photutils']}
    result['calibration_files']={str(calpath(kind,6).relative_to(ROOT)):sha(calpath(kind,6)) for kind in ['solid_angle_pixel_map','spectral_wcs']}
    (OUT/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'written':str(OUT/'results.json'),'production_unchanged':before==after,'real_frames':sum(len(t['frames']) for t in result['real_targets']),'versions':result['versions']}))

def epsf_phase(epsf,ox,oy):
    from photutils.psf import ImagePSF
    model=ImagePSF(epsf,oversampling=(oy,ox)); yy,xx=np.mgrid[-6:7,-6:7]
    norms=[];differences=[];fractions=[]
    for fx in [0,.2,.4,.6,.8]:
        for fy in [0,.2,.4,.6,.8]:
            independent=model.evaluate(xx,yy,1,fx,fy); independent/=independent.sum()
            ours=map_coordinates(epsf,[(yy-fy)*oy+(epsf.shape[0]-1)/2,(xx-fx)*ox+(epsf.shape[1]-1)/2],order=3,mode='constant',cval=0)/(epsf.sum()/(ox*oy))
            norms.append(float(ours.sum())); differences.append(float(np.max(abs(ours-independent))));fractions.append(float(ours[(xx-fx)**2+(yy-fy)**2<=(12.4/6.2)**2].sum()))
    return {'label':'Real ePSF models evaluated at synthetic pixel phases; not simulated observations','application_stamp_sum_range':[min(norms),max(norms)],'max_pixel_profile_difference_to_normalized_Photutils':max(differences),'radius_2pixel_profile_fraction_range':[min(fractions),max(fractions)]}

def synthetic_controls():
    rng=np.random.default_rng(20261114); yy,xx=np.mgrid[-8:9,-8:9]; sigma=1.0
    def gaussian(x,y):
        return .25*(erf((xx+.5-x)/(np.sqrt(2)*sigma))-erf((xx-.5-x)/(np.sqrt(2)*sigma)))*(erf((yy+.5-y)/(np.sqrt(2)*sigma))-erf((yy-.5-y)/(np.sqrt(2)*sigma)))
    p=gaussian(0,0); X=np.column_stack([p.ravel(),np.ones(p.size),xx.ravel(),yy.ravel()]); weights=np.linalg.pinv(X)[0].reshape(p.shape)
    out={'label':'SYNTHETIC controls. Independent pixel-integrated Gaussian, sigma=1 pixel; no SPHEREx detections.'}
    rows=[]
    for shift in [0,.2,.5,1]:
        image=10*gaussian(shift,0)+3+.1*xx-.05*yy
        beta=np.linalg.lstsq(X,image.ravel(),rcond=None)[0]; resid=image.ravel()-X@beta
        # Add expectation of unit-variance independent Gaussian noise: chi2~1+model mismatch/dof.
        rows.append({'true_shift_pixels':shift,'true_flux':10,'fixed_position_fitted_flux':float(beta[0]),'expected_chi2_with_unit_noise':float(1+resid@resid/(p.size-4))})
    out['position_bias']=rows
    a=xx**2+yy**2<=2**2;bg=(xx**2+yy**2>=3.6**2)&(xx**2+yy**2<=6**2)
    w=np.zeros(p.shape);w[a]=1;w[bg]=-a.sum()/bg.sum()
    fixed=100*p+3;gradient=fixed+.1*xx-.05*yy;neighbor=fixed+100*gaussian(4,0)
    nb=bg&(xx>=0);wm=np.zeros(p.shape);wm[a]=1;wm[nb]=-a.sum()/nb.sum()
    values=rng.normal(size=(3000,p.size))@w.ravel()
    out['aperture']={'a_pixels':int(a.sum()),'bg_pixels':int(bg.sum()),'expected_random_variance':float(np.sum(w*w)),'monte_carlo_variance_3000':float(np.var(values,ddof=1)),
                     'fixed_source_flux':float(np.sum(w*fixed)),'uniform_background_plus_20_flux':float(np.sum(w*(fixed+20))),
                     'symmetric_gradient_flux':float(np.sum(w*gradient)),'masked_one_side_gradient_flux':float(np.sum(wm*gradient)),
                     'neighbor_unmasked_flux':float(np.sum(w*neighbor)), 'injected_total_source_flux':100}
    # Exact bilinear weights for a half-pixel shift of a 4x4 output sum.
    W=np.zeros((16,25))
    for y in range(4):
        for x in range(4):
            for dy in [0,1]:
                for dx in [0,1]:W[y*4+x,(y+dy)*5+x+dx]=.25
    C=W@W.T
    out['bilinear_noise']={'single_output_variance':float(C[0,0]),'neighbor_correlation':float(C[0,1]/np.sqrt(C[0,0]*C[1,1])),
                          'sum16_diagonal_variance':float(np.trace(C)),'sum16_full_variance':float(C.sum()),'sum_error_underestimate_factor':float(np.sqrt(C.sum()/np.trace(C)))}
    from reproject import reproject_interp
    hi=WCS(naxis=2);hi.wcs.crval=[133,-7];hi.wcs.crpix=[9,9];hi.wcs.cdelt=[-6.2/3600,6.2/3600];hi.wcs.ctype=['RA---TAN','DEC--TAN']
    ho=hi.deepcopy();ho.wcs.crpix += [.5,.5]
    flat,_=reproject_interp((np.full(p.shape,7.),hi),ho,shape_out=p.shape,order='bilinear')
    img,_=reproject_interp((p,hi),ho,shape_out=p.shape,order='bilinear')
    out['bilinear_image']={'constant_sb_max_error':float(np.nanmax(abs(flat-7))), 'gaussian_sum_in':float(p.sum()),'gaussian_sum_out':float(np.nansum(img)),
                           'second_moment_in':float(np.sum(p*(xx**2+yy**2))/p.sum()),'second_moment_out_about_shifted_center':float(np.nansum(img*((xx-.5)**2+(yy-.5)**2))/np.nansum(img))}
    l1,l2=4.417173913268159,4.423067110042768
    out['band_powerlaws']=[{'slope_p':p,'ratio_Fnu_lambda2_over_lambda1':(l2/l1)**p} for p in [-2,0,2,10,20]]
    # Identical central wavelength/FWHM, different wings, smooth continuum plus a synthetic narrow absorption feature.
    lam=np.linspace(4.35,4.5,20001);c=4.42;bw=.035
    r1=(abs(lam-c)<=bw/2).astype(float);r2=np.exp(-4*np.log(2)*((lam-c)/bw)**2)
    sed=1-.8*np.exp(-.5*((lam-(c+.018))/.003)**2)
    mean=lambda r:float(np.trapezoid(sed*r,lam)/np.trapezoid(r,lam))
    out['same_center_fwhm_different_response']={'top_hat_band_mean':mean(r1),'gaussian_band_mean':mean(r2),'label':'Synthetic response/SED, not measured SPHEREx transmission or molecular detection.'}
    return out

def reference_control(m):
    from backend.reference_spectra import compare_reference
    local=get('irsa_result','2136c5099162463189f514ddc83c44f0'); f=m['frames'][1]
    content='wavelength,flux,flux_err,mjd,ra,dec,det_id\n'+f"1.2,1000,100,{f['mjd']},{local['ra']},{local['dec']},6\n"
    # Prevent the sole persistence action; no connection or cache writes occur.
    with patch('backend.reference_spectra.store.put'):
        r=compare_reference(local,m,content,'csv')
    return {'label':'Synthetic invalid reference row; not IRSA data','wrong_reference_wavelength_um':1.2,'local_wavelength_um':local['rows'][1]['wavelength_um'],
            'release_provided':False,'matched_count':r['matched_count'],'matches':[v for v in r['matches'] if v['matched']]}

if __name__=='__main__':
    main()
