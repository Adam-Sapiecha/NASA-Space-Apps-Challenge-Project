"""Supplementary read-only real-FITS/route/astrometry controls; audit outputs only."""
import json
import numpy as np
from audit_math_physics import ROOT, OUT, get, native_path, calpath, map_from_parent, motion, vec, angular, aperture_weights, sha, BAD
from astropy.coordinates import SkyCoord, get_body_barycentric
from astropy import units as u
from astropy.io import fits
from astropy.time import Time
from astropy.wcs import WCS
from scipy.ndimage import map_coordinates

def main():
    five=json.loads((ROOT/'data/audit/five-targets-final.json').read_text(encoding='utf-8'))
    output={'astrometry':[], 'route_evidence':{},'real_background_controls':[], 'epsilon_without_annulus_gate':[]}
    for item in five['targets']:
        t=item['target'];m=get('analysis',item['analysis_id']); times=np.array([f['mjd'] for f in m['frames']]); n=vec(t['ra_deg'],t['dec_deg'])
        pm=motion(t,times); earth=get_body_barycentric('earth',Time(times,format='mjd')).xyz.to_value(u.au).T
        par=-t['parallax_mas']*np.deg2rad(1/3600000)*(earth-np.sum(earth*n,axis=1)[:,None]*n)
        apparent=pm+par;apparent/=np.linalg.norm(apparent,axis=1)[:,None]
        row={'id':t['id'],'pm_plus_earth_parallax_first_last_arcsec':float(angular(apparent[0],apparent[-1]))}
        if t['id']=='wise0855':
            row['nov_apr']={'baseline_days':float(times[3]-times[1]),'proper_motion_shift_arcsec':float(angular(pm[1],pm[3])),
                            'earth_parallax_vector_change_arcsec':float(np.rad2deg(np.linalg.norm(par[3]-par[1]))*3600),
                            'combined_shift_arcsec':float(angular(apparent[1],apparent[3]))}
            route_evidence(m,output)
            background_controls(m,output)
        if t['id']=='epsilon-indi-b':
            eps_indi_control(item,m,output)
        output['astrometry'].append(row)
    native_montage(five)
    r=json.loads((OUT/'results.json').read_text(encoding='utf-8'))
    output['hashes_all_22_native_unchanged']={name:sha(ROOT/name)==value for name,value in r['source_hashes'].items()}
    output['hashes_both_D6_calibrations_unchanged']={name:sha(ROOT/name)==value for name,value in r['calibration_files'].items()}
    output['current_production_hashes']=__import__('audit_math_physics').snapshot()
    (OUT/'supplement.json').write_text(json.dumps(output,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in output.items() if k not in ['current_production_hashes','hashes_all_22_native_unchanged']},ensure_ascii=False))

def eps_indi_control(item,m,out):
    from backend.calibrated import psf_at,fit_epsf
    for f in m['frames']:
        row={'id':f['id'],'date':f['date'],'label':'Exploratory control bypassing annulus prerequisite; not an approved production measurement or identified source.'}
        try:
            s=next(s for s in item['samples'] if s['frame_id']==f['id']);c=SkyCoord(s['prediction']['ra'],s['prediction']['dec'],unit='deg')
            with fits.open(native_path(m,f),memmap=False) as h:
                data=np.array(h['IMAGE'].data,float);v=np.array(h['VARIANCE'].data,float);flags=np.array(h['FLAGS'].data,np.uint32);w=WCS(h['IMAGE'].header);x,y=map(float,w.world_to_pixel(c))
                if not (0<=x<data.shape[1] and 0<=y<data.shape[0]):raise ValueError('Predicted position outside native cutout.')
                area,_=map_from_parent(calpath('solid_angle_pixel_map',2),'IMAGE',h['IMAGE'].header,data.shape);k=area*1e9*(np.pi/(180*3600))**2
                mask=sum(1<<b for name,b in f['flag_definitions'].items() if name in BAD)
                valid=np.isfinite(data)&np.isfinite(v)&(v>0)&((flags&mask)==0)
                epsf,meta=psf_at(h,x,y);row['fit']=fit_epsf(data,v,valid,k,x,y,epsf,meta['oversample_x'],meta['oversample_y']);row['zone']=meta
                row['position_sensitivity']=[dict(dx_pixels=delta,**fit_epsf(data,v,valid,k,x+delta,y,epsf,meta['oversample_x'],meta['oversample_y'])) for delta in [-.5,.5]]
        except (ValueError,FileNotFoundError) as e:row['reason']=str(e)
        out['epsilon_without_annulus_gate'].append(row)

def route_evidence(m,out):
    from backend.evidence import evidence
    f1,f2=m['frames'][1],m['frames'][3];point={'x':.5,'y':.5}; anchors=[dict(frameId=f['id'],mjd=f['mjd'],x=x,y=y) for f,x,y in [(f1,.6,.4),(f2,.4,.6)]]
    note=dict(id='SYNTHETIC-AUDIT-NOTE-NOT-SAVED',created_at='2026-11-14',frame_ids=[f1['id'],f2['id']],point=point,anchors=anchors,mode='route',kind='uncertain',text='Synthetic route annotation on real images; not detections.',route_checks={})
    e=evidence(note,m)
    for a,s in zip(anchors,e['sources']):
        n=m['pixels'];px=min(n-1,int(a['x']*n));py=n-1-min(n-1,int(a['y']*n))
        with np.load(ROOT/'data/analyses'/m['id']/f"{a['frameId']}.npz") as d:
            out['route_evidence'][a['frameId']]={'exported_wavelength_um':s['wavelength_um'],'marker_pixel_wavelength_um':float(d['wavelength'][py,px]),'marker_xy':[a['x'],a['y']],'exported_location':s['wavelength_location']}

def background_controls(m,out):
    """Real flux/error and gradient robustness at predeclared blank-field points.

    No assertion of source-free/stable astrophysical truth: check empirical sky
    model against native pixels and flags rather than just a synthetic image.
    """
    points=[(.3,.3),(.7,.7),(.3,.7),(.7,.3)]
    skyw=WCS(m['wcs']);n=m['pixels']
    for frame in [m['frames'][1],m['frames'][3]]:
        with fits.open(native_path(m,frame),memmap=False) as h:
            data=np.array(h['IMAGE'].data,float);v=np.array(h['VARIANCE'].data,float);flags=np.array(h['FLAGS'].data,np.uint32);w=WCS(h['IMAGE'].header)
            area,_=map_from_parent(calpath('solid_angle_pixel_map',6),'IMAGE',h['IMAGE'].header,data.shape); k=area*1e9*(np.pi/(180*3600))**2
            yy,xx=np.indices(data.shape)
            for x,y in points:
                c=skyw.pixel_to_world(x*n-.5,(1-y)*n-.5);r,a,bg,valid=aperture_weights(data,v,flags,frame,w,c,k)
                record={'id':frame['id'],'point':[x,y],'mean_background_aperture':r}
                if r['valid']:
                    sx,sy=w.world_to_pixel(c);X=np.column_stack([np.ones(bg.sum()),xx[bg]-sx,yy[bg]-sy]);weight=1/np.sqrt(v[bg]);beta=np.linalg.lstsq(X*weight[:,None],data[bg]*weight,rcond=None)[0]
                    pred=beta[0]+beta[1]*(xx-sx)+beta[2]*(yy-sy)
                    record['plane_background_flux_mjy']=float(np.sum((data[a]-pred[a])*k[a]))
                    record['plane_gradient_sb_per_pixel']=list(beta[1:])
                    record['background_standardized_residual_rms']=float(np.sqrt(np.mean(((data[bg]-pred[bg])/np.sqrt(v[bg]))**2)))
                out['real_background_controls'].append(record)

def native_montage(five):
    import os,sys
    sys.path.insert(0,str(ROOT/'.cache/audit-plot-libs'))
    os.environ['MPLCONFIGDIR']=str(OUT/'matplotlib-cache')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import AsinhNorm
    from matplotlib.patches import Circle
    fig,axes=plt.subplots(1,5,figsize=(16,4.8),constrained_layout=True)
    for item,ax in zip(five['targets'],axes):
        t=item['target'];m=get('analysis',item['analysis_id']);f=m['frames'][1 if t['id'] in ['barnard','wise0855'] else 0]
        s=next(s for s in item['samples'] if s['frame_id']==f['id']);c=SkyCoord(s['prediction']['ra'],s['prediction']['dec'],unit='deg')
        with fits.open(native_path(m,f)) as h:
            d=np.array(h['IMAGE'].data,float);w=WCS(h['IMAGE'].header);flags=h['FLAGS'].data;xx,yy=w.world_to_pixel(c)
            lo,hi=np.nanpercentile(d,[5,99]);ax.imshow(d,origin='lower',cmap='gray',norm=AsinhNorm(linear_width=max((hi-lo)/15,1e-10),vmin=lo,vmax=hi))
            ax.add_patch(Circle((xx,yy),2,fill=False,color='#ffb600',lw=1.5));ax.plot(xx,yy,'+',color='#ffb600',ms=10)
            ax.set_title(t['name']+'\n'+f['date'][:10],fontsize=11)
            ax.set_xlim(max(0,float(xx)-12),min(d.shape[1]-1,float(xx)+12));ax.set_ylim(max(0,float(yy)-12),min(d.shape[0]-1,float(yy)+12));ax.set_xlabel('Native x [pixel]')
    axes[0].set_ylabel('Native y [pixel]')
    fig.suptitle('REAL NATIVE FITS | circles = catalogue predictions, not identified detections\nIndependent display scales per field; brightness cannot be compared between panels',fontsize=13)
    fig.savefig(OUT/'native_fields.png',dpi=150);plt.close(fig)

if __name__=='__main__':main()
