"""Read-only audit of concurrently added modules. No jobs, training or DB writes."""
import json
from unittest.mock import patch
from audit_math_physics import ROOT,OUT,DB,get,native_path,snapshot,motion,angular

def main():
    from backend.native_diagnostics import native_profile
    from backend.trajectory import linear_motion
    from astropy.coordinates import SkyCoord
    from astropy import units as u
    five=json.loads((ROOT/'data/audit/five-targets-final.json').read_text(encoding='utf-8'))
    before=snapshot();out={'real_centroids':[], 'db_counts':dict(DB.execute('SELECT kind,COUNT(*) FROM records GROUP BY kind').fetchall()),
                           'artifact_active':get('artifact_active','current')}
    for item in five['targets']:
        m=get('analysis',item['analysis_id'])
        for sample in item['samples']:
            f=next(f for f in m['frames'] if f['id']==sample['frame_id']);row={'target':item['target']['id'],'frame_id':f['id']}
            try:
                with patch('backend.native_diagnostics.download_path',lambda *args:native_path(m,f)):
                    row['fit']=native_profile(m,**sample['point'],frame_id=f['id'])
            except Exception as e:row['reason']=str(e)
            out['real_centroids'].append(row)
    origin=SkyCoord(359.999,67,unit='deg');obs=[]
    for dt in [0,3,10,20]:
        c=origin.spherical_offsets_by((.8*dt)*u.arcsec,(-.3*dt)*u.arcsec)
        obs.append(dict(ra=float(c.ra.deg),dec=float(c.dec.deg),mjd=61000+dt,error_arcsec=1.2))
    out['synthetic_linear_motion']=linear_motion(obs,[61010,61030])
    from backend.artifact_model import connected_groups,readiness
    # Different cutouts from one original exposure, without exposure ID in grouping.
    examples=[dict(analysis_id='synthetic-A',source_id='synthetic-a',y=0,profile=dict(ra=20,dec=0,source_sha256='cutout-A',obs_id='SAME_ORIGINAL_EXPOSURE')),
              dict(analysis_id='synthetic-B',source_id='synthetic-b',y=1,profile=dict(ra=20.05,dec=0,source_sha256='cutout-B',obs_id='SAME_ORIGINAL_EXPOSURE'))]
    out['synthetic_group_overlap_control']={'groups':connected_groups(examples),'separation_arcsec':180,'original_exposure_shared':True,
                                           'label':'Synthetic metadata, no classifier trained/activated.'}
    out['binomial_retention_control']={'successes':5,'trials':5,'point_estimate':1.,'one_sided_95pct_lower_bound':.05**(1/5),
                                       'independent_successes_needed_for_95pct_lower_bound_at_least_95pct':59}
    # Important: SIMBAD J2000 coordinates were transported from Gaia's 2016
    # position, while PM remains the Gaia-era value. Do not interpret the 26yr
    # sensitivity in the first script as a measured 0.44 arcsec position error.
    t=five['targets'][0]['target'];m=get('analysis',five['targets'][0]['analysis_id']);tt=[f['mjd'] for f in m['frames']]
    gaia=dict(t,ra_deg=269.44850252544,dec_deg=4.73942005111,epoch_mjd=57388.5)
    out['barnard_original_gaia2016']={'source_id':'4472832130942575872','reference_mjd':57388.5,'radial_velocity_kms':-110.47,
        'offset_from_production_prediction_arcsec':angular(motion(t,tt),motion(gaia,tt,-110.47)).tolist(),
        'caveat':'Requires internally consistent original Gaia epoch; replaces naive 26-year perspective-offset interpretation.'}
    for target in ['wise0855','epsilon-indi-b']:
        rows=[r for r in out['real_centroids'] if r['target']==target and r.get('fit')]
        if target=='wise0855':rows=[r for r in rows if r['frame_id'] in ['4432acd4afc90868d16b','79ad233baf786e452cbd']]
        a,b=rows[0]['fit'],rows[-1]['fit']
        c1,c2=SkyCoord(a['ra'],a['dec'],unit='deg'),SkyCoord(b['ra'],b['dec'],unit='deg')
        out[target+'_centroid_first_last']={'separation_arcsec':float(c1.separation(c2).arcsec),'independent_axis_error_difference_arcsec':float(__import__('math').hypot(a['error_arcsec'],b['error_arcsec'])),
                                          'warning':'Exploratory 2 arcsec floor, no field astrometric calibration; not significance or identification.'}
    out['production_hashes_at_start']=before;out['production_hashes_at_end']=snapshot()
    out['production_changed_during_this_check']=[k for k in before if before[k]!=out['production_hashes_at_end'].get(k)]
    (OUT/'recent_extensions.json').write_text(json.dumps(out,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'written':'recent_extensions.json','fits':len(out['real_centroids']),'artifact_active':out['artifact_active'],'changed':out['production_changed_during_this_check']}))

if __name__=='__main__':main()
