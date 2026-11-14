"""Package an allowlisted demo subset, never the user's full SQLite workspace.

Creates a new seed SQLite DB and ZIP. Does not modify or delete original data.
"""
import hashlib
import json
import sqlite3
import sys
import zipfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from astropy.coordinates import SkyCoord
from backend import store
from backend.science import download_path


def main():
    output=ROOT/'.cache/demo-seed.zip'
    folder=Path(tempfile.mkdtemp(prefix='demo-seed-build-',dir=ROOT/'.cache'))
    dbpath=folder/'workspace.sqlite'
    if dbpath.exists():
        raise FileExistsError('Seed already exists; choose a new build directory rather than overwriting it.')
    report=json.loads((store.ROOT/'audit/five-targets-final.json').read_text(encoding='utf-8'))
    spectral=json.loads((store.ROOT/'spectral_demo.json').read_text(encoding='utf-8'))
    ids={t['analysis_id'] for t in report['targets']} | {spectral.get('id') or spectral['analysis_id']}
    motion=json.loads((ROOT/'frontend/src/motionShowcase.json').read_text(encoding='utf-8'))
    ids.add(motion['analysis_id'])
    prediction=json.loads((ROOT/'frontend/public/prediction-demo/report.json').read_text(encoding='utf-8'))
    ids.add(prediction['analysis_id'])
    records=[];files={};missing=[]
    for id in sorted(ids):
        manifest=store.get('analysis',id)
        if not manifest:raise ValueError('Missing analysis '+id)
        records.extend([('analysis',id,manifest),('search',manifest['search']['id'],manifest['search']),
                        ('job',id,dict(id=id,status='complete',message='Restored prepared demo'))])
        for path in (store.ROOT/'analyses'/id).iterdir():
            if path.is_file() and path.suffix in ('.fits','.png','.npz','.json'):
                files[str(path.relative_to(store.ROOT)).replace('\\','/')]=path
        centre=SkyCoord(manifest['search']['ra'],manifest['search']['dec'],unit='deg')
        for frame in manifest['frames']:
            path=download_path(frame,centre,manifest['search']['fov_arcmin'])
            if not path.exists():missing.append(frame['id'])
            else:files['fits/'+path.name]=path
    # Only audit-computed measurements are included; no personal notes or jobs.
    measurement_ids={s['measurement_id'] for t in report['targets'] for s in t.get('samples',[]) if s.get('measurement_id')}
    if len(sys.argv)>1:
        note=store.get('note',sys.argv[1])
        if not note or note['analysis_id'] not in ids:raise ValueError('Explicit demo note must belong to an included analysis.')
        records.append(('note',note['id'],note))
        if note.get('measurement_id'):measurement_ids.add(note['measurement_id'])
    for id in sorted(measurement_ids):
        value=store.get('measurement',id)
        if value:records.append(('measurement',id,value))
    with sqlite3.connect(dbpath) as db:
        db.execute('CREATE TABLE records (kind TEXT,id TEXT,body TEXT,PRIMARY KEY(kind,id))')
        db.executemany('INSERT OR REPLACE INTO records VALUES (?,?,?)',[(k,id,json.dumps(v,allow_nan=False)) for k,id,v in records])
    files['workspace.sqlite']=dbpath
    for name in ('five-targets-final.json','independent-photutils.json'):
        path=store.ROOT/'audit'/name
        if path.exists():files['audit/'+name]=path
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as bundle:
        for name,path in sorted(files.items()):bundle.write(path,name)
        wise=next(t for t in report['targets'] if t['target']['id']=='wise0855')
        bundle.writestr('demo.json',json.dumps(dict(id=wise['analysis_id'],label='Pole WISE 0855 — identyfikacja niepotwierdzona')))
        bundle.writestr('SEED_INFO.json',json.dumps(dict(created_at=datetime.now(timezone.utc).isoformat(),analysis_ids=sorted(ids),missing_native_fits=missing,
                          note='Public astronomical products and scripted audit measurements only. No user notes, credentials or observer locations.'),indent=2))
    result=dict(path=str(output),bytes=output.stat().st_size,sha256=hashlib.sha256(output.read_bytes()).hexdigest(),analyses=len(ids),files=len(files),missing_native_fits=missing)
    (store.ROOT/'audit/demo-seed.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
