"""Generate a self-contained English replay from actual saved NASA images.

No requests, generated sky data, interpolation of gaps, or discovery claims.
The full RA/Dec search remains in the existing application.
"""
import base64
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from backend import store


def main():
    audit=json.loads((store.ROOT/'audit/five-targets-final.json').read_text(encoding='utf-8'))
    wise=next(t for t in audit['targets'] if t['target']['id']=='wise0855')
    spectral=json.loads((store.ROOT/'spectral_demo.json').read_text(encoding='utf-8'))
    spectral_id=spectral.get('id') or spectral.get('analysis_id')
    if not spectral_id:
        raise ValueError('Spectral demo has no analysis ID.')
    sets=[]
    for id,label,mode in [(wise['analysis_id'],'Time: WISE 0855 field','time'),(spectral_id,'Wavelengths: a real SPHEREx field','wavelength')]:
        manifest=store.get('analysis',id)
        frames=manifest['frames']
        if mode=='time':
            # Largest-baseline pair with adequate field coverage and close centre bands.
            pairs=[(abs(a['mjd']-b['mjd']),[a,b]) for i,a in enumerate(frames) for b in frames[i+1:]
                   if min(a['coverage'],b['coverage'])>=.8 and a['mjd']!=b['mjd']
                   and abs(a['wavelength_um']-b['wavelength_um'])<=min(a['bandwidth_um'],b['bandwidth_um'])/2]
            if not pairs:raise ValueError('No browsing-compatible time pair.')
            frames=max(pairs,key=lambda p:p[0])[1]
        else:frames=sorted(frames,key=lambda f:f['wavelength_um'])
        rows=[]
        for frame in frames:
            image=store.ROOT/'analyses'/id/f"{frame['id']}.png"
            rows.append(dict(id=frame['id'],obs_id=frame['obs_id'],date=frame['date'],mjd=frame['mjd'],
                             wavelength_um=frame['wavelength_um'],bandwidth_um=frame['bandwidth_um'],band=frame['band'],
                             url=frame['url'],sha256=frame['sha256'],coverage=frame['coverage'],
                             image='data:image/png;base64,'+base64.b64encode(image.read_bytes()).decode('ascii')))
        sets.append(dict(label=label,mode=mode,analysis_id=id,ra=manifest['search']['ra'],dec=manifest['search']['dec'],
                         fov=manifest['search']['fov_arcmin'],collection=manifest['search']['collection'],
                         frames=rows,failures=len(manifest['failures']),display=manifest['display']))
    payload=dict(sets=sets,checked_at=audit['checked_at'],five=[dict(name=t['target']['name'],analysis_id=t['analysis_id'],
                 prepared=t['prepared'],selected=t['selected'],valid_apertures=t['valid_predicted_apertures'],
                 pairs=len(t['comparable_pairs']),result=t['result']) for t in audit['targets']])
    template=(ROOT/'scripts/demo_template.html').read_text(encoding='utf-8')
    folder=ROOT/'frontend/public/demo';folder.mkdir(parents=True,exist_ok=True)
    page=template.replace('__DEMO_JSON__',json.dumps(payload,ensure_ascii=True,allow_nan=False).replace('<','\\u003c'))
    (folder/'index.html').write_text(page,encoding='utf-8')
    print(folder/'index.html',len(page),'characters')


if __name__=='__main__':main()
