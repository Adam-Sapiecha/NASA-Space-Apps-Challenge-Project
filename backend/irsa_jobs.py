"""Bounded IRSA-related jobs using the application's existing worker process."""
import hashlib
import json
from datetime import datetime,timezone

from astropy.table import Table

from backend import store


def run_job(id,kind,manifest,settings):
    try:
        def progress(i,total):
            store.put('job',id,dict(id=id,status='running',completed=i,total=total,message=f'IRSA: {kind} {i+1}/{total}'))
        progress(0,1)
        if kind=='calibrated':
            from backend.calibrated import calibrated_report
            result=calibrated_report(manifest,**settings,progress=progress)
        elif kind=='discovery':
            from backend.source_discovery import discover
            result=discover(manifest,**settings,progress=progress)
        elif kind=='most':
            from backend.moving_objects import search_moving
            result=search_moving(**settings)
        elif kind=='context':
            from backend.object_context import context
            result=context(manifest, **settings, progress=progress)
        elif kind=='profile':
            from backend.native_diagnostics import profile_series
            from backend.source_assessment import source_record
            from backend.artifact_model import assess_profile
            result=profile_series(manifest, **settings, progress=progress)
            source=source_record(manifest, **settings)
            result['source_id']=source['id']
            for row in result['rows']:
                if row.get('valid'):
                    store.put('artifact_features', source['id']+':'+row['frame_id'], row)
                    row['assessment']=assess_profile(row)
        elif kind=='ephemeris':
            from backend.trajectory import ephemeris
            result=ephemeris(**settings)
        elif kind=='motion':
            from backend.native_diagnostics import native_profile
            from backend.trajectory import linear_motion
            positions=settings['positions']
            observations=[]
            for i, position in enumerate(positions):
                progress(i,len(positions))
                row=native_profile(manifest, **position, systematic_floor_arcsec=settings['systematic_floor_arcsec'])
                if row['snr'] < 5 or row['reduced_chi2'] > 3:
                    raise ValueError('Słabe dopasowanie pozycji; sprawdź wskazanie źródła i diagnostykę PSF.')
                observations.append(row)
            result=linear_motion(observations,settings['prediction_mjds'])
            result['positions']=positions
        elif kind=='spectrum_model':
            from backend.spectral_models import interpret
            options=dict(settings)
            reference=store.get('irsa_result',options.pop('calibrated_id'))
            if reference is None: raise ValueError('Brak raportu kalibracji.')
            result=interpret(reference,**options)
        elif kind=='artifact_training':
            from backend.artifact_model import train
            result=dict(kind='artifact_training', **train())
        else:
            raise ValueError('Nieobsługiwane zadanie.')
        result.update(id=id,created_at=datetime.now(timezone.utc).isoformat(),settings=settings)
        if manifest:result['analysis_id']=manifest['id']
        folder=store.ROOT/'irsa'/id;folder.mkdir(parents=True,exist_ok=True)
        if kind=='calibrated':
            Table(dict(ra=[result['ra']],dec=[result['dec']])).write(folder/'target.tbl',format='ascii.ipac',overwrite=True)
        (folder/'report.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8')
        store.put('irsa_result',id,result)
        store.put('job',id,dict(id=id,status='complete',completed=1,total=1,message='Wynik IRSA gotowy'))
    except Exception as exc:
        store.put('job',id,dict(id=id,status='failed',message=f'{type(exc).__name__}: {exc}'[:2000]))
