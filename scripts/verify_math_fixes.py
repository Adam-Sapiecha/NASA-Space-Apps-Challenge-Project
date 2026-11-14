"""Offline verification on real cached FITS; original DB and inputs stay read-only.

Only a new audit JSON is written. Synthetic CSVs test the importer; they are not
Tractor exports or scientific validation. No source is claimed as discovered.
"""
import hashlib
import json
import sqlite3
import sys
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from astropy.io import fits
from backend import store
from backend.measurements import measure
from backend.calibrated import calibrated_report,psf_at
from backend.photometry_math import epsf_profile
from backend.reference_spectra import compare_reference


def main():
    out=ROOT/'data/audit/math_fixes_20261114';out.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect('file:'+(ROOT/'data/workspace.sqlite').as_posix()+'?mode=ro',uri=True)
    def get(kind,key):
        if kind=='measurement':return None
        row=db.execute('SELECT body FROM records WHERE kind=? AND id=?',(kind,key)).fetchone()
        return json.loads(row[0]) if row else None
    five=json.loads((ROOT/'data/audit/five-targets-final.json').read_text(encoding='utf-8'))
    old=json.loads((ROOT/'data/audit/math_physics_20261114/results.json').read_text(encoding='utf-8'))
    original_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in old['source_hashes']}
    result=dict(utc=datetime.now(timezone.utc).isoformat(),targets=[],real_wise=None,synthetic_reference_checks={})
    with patch.object(store,'get',get),patch.object(store,'put'):
        for item in five['targets']:
            manifest=get('analysis',item['analysis_id']);rows=[]
            for sample in item['samples']:
                frame=next(f for f in manifest['frames'] if f['id']==sample['frame_id'])
                single=dict(manifest,id=manifest['id']+'-verification-'+frame['id'],frames=[frame])
                measured=measure(single,**sample['point'],radius_arcsec=12.4)
                rows.append(measured['rows'][0])
            result['targets'].append(dict(id=item['target']['id'],rows=rows,valid_count=sum(r['valid'] for r in rows)))
        manifest=get('analysis','4812094a2ce843a8b787837eb13ec845')
        cal=calibrated_report(manifest,.5,.5,12.4);cal['id']='offline-real-fits-verification'
        result['real_wise']=cal
        row=cal['rows'][1];frame=manifest['frames'][1]
        header='wavelength,flux,flux_err,mjd,ra,dec,det_id,data_collection,lvf_id,lambda_width\n'
        content=header+f"{row['wavelength_um']},1000,100,{row['mjd']},{cal['ra']},{cal['dec']},6,dr1,{frame['obs_id']},{row['bandwidth_um']}\n"
        controls={'compatible_metadata':content,'wrong_wavelength':content.replace(str(row['wavelength_um']),'1.2'),
                  'missing_release':content.replace(',dr1,',',,'),'wrong_exposure':content.replace(frame['obs_id'],'2025W46_1A_9999_1')}
        for name,csv in controls.items():
            r=compare_reference(cal,manifest,csv,'csv')
            result['synthetic_reference_checks'][name]=r['matched_count']
        result['synthetic_reference_checks']['label']='Synthetic CSV rows, not real IRSA exports.'
        assert result['synthetic_reference_checks']['compatible_metadata']==1
        assert all(result['synthetic_reference_checks'][n]==0 for n in ['wrong_wavelength','missing_release','wrong_exposure'])
        # Real supplied ePSF, evaluated at controlled phases, not simulated observations.
        s=manifest['search'];params=dict(center=f"{s['ra']},{s['dec']}d",size=str(s['fov_arcmin']/60))
        path=ROOT/'data/fits'/(hashlib.sha256((frame['url']+json.dumps(params,sort_keys=True)).encode()).hexdigest()+'.fits')
        with fits.open(path) as hd:
            e,info=psf_at(hd,28.718157305870637,28.51085807366734)
            sums=[float(epsf_profile((17,17),8+dx,8+dy,e,info['oversample_x'],info['oversample_y']).sum()) for dx in [0,.2,.4,.6,.8] for dy in [0,.2,.4,.6,.8]]
        result['epsf_phase_sum_range']=[min(sums),max(sums)]
        assert np.allclose(sums,1,rtol=0,atol=1e-12)
    result['original_native_files_unchanged']=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in original_hashes.items())
    assert result['original_native_files_unchanged']
    result['database_writes']=0
    (out/'offline-validation.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    print(json.dumps(dict(path=str(out/'offline-validation.json'),targets=[dict(id=t['id'],valid=t['valid_count'],total=len(t['rows'])) for t in result['targets']],phase_sum_range=result['epsf_phase_sum_range'],original_files_unchanged=result['original_native_files_unchanged']),ensure_ascii=False))


if __name__=='__main__':main()
