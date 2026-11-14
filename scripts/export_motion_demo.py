"""Export two real, fixed-WCS images for the curated 3I/ATLAS motion example."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from scipy.ndimage import maximum_filter
from backend import store
from backend.science import stretch_rgba
from PIL import Image


def main():
    ident = 'motion3iatlas20251214d6'
    folder = store.ROOT/'analyses'/ident
    m = json.loads((folder/'manifest.json').read_text())
    evidence = json.loads((store.ROOT/'audit'/f'{ident}-candidate.json').read_text())
    arrays = [fits.getdata(folder/(f['id']+'.fits')).astype(float) for f in m['frames']]
    points = [e['predicted_pixel'] for e in evidence['evidence']]
    bg = [float(np.nanmedian(a)) for a in arrays]
    residuals = [a-b for a,b in zip(arrays,bg)]
    values = np.concatenate([a[np.isfinite(a)] for a in residuals])
    low, high = map(float,np.percentile(values,[1,99.8]))
    yy, xx = np.indices(arrays[0].shape)
    controls_mask = np.isfinite(arrays[0]) & np.isfinite(arrays[1])
    for x,y in points:
        controls_mask &= np.hypot(xx-x,yy-y)>9
    controls_mask &= (xx>6)&(yy>6)&(xx<len(xx)-7)&(yy<len(xx)-7)
    # Cross-check separated stationary local maxima in the same celestial WCS.
    maxima = controls_mask & (residuals[0] == maximum_filter(np.nan_to_num(residuals[0],nan=-1e9),size=7))
    candidates = sorted(zip(*np.where(maxima)),key=lambda p:-residuals[0][p])
    controls=[]
    for y,x in candidates:
        if any(np.hypot(x-c['a_peak'][0],y-c['a_peak'][1])<8 for c in controls):continue
        box=residuals[1][y-2:y+3,x-2:x+3]
        if not np.isfinite(box).all():continue
        dy,dx=np.unravel_index(np.argmax(box),box.shape)
        px,py=int(x+dx-2),int(y+dy-2)
        if residuals[0][y,x] <= 0 or residuals[1][py,px] <= 0:continue
        controls.append(dict(a_peak=[int(x),int(y)],b_peak=[px,py],offset_pixels=float(np.hypot(px-x,py-y))))
        if len(controls)==5:break
    coords=SkyCoord([e['prediction_ra'] for e in evidence['evidence']],
                    [e['prediction_dec'] for e in evidence['evidence']],unit='deg')
    minutes=(m['frames'][1]['mjd']-m['frames'][0]['mjd'])*1440
    report=dict(analysis_id=ident,object='3I/ATLAS',minutes=minutes,
        predicted_separation_arcmin=float(coords[0].separation(coords[1]).arcmin),
        image_pixels=m['pixels'],field_arcmin=m['search']['fov_arcmin'],
        measured_peak_separation_pixels=float(np.linalg.norm(np.array(evidence['evidence'][1]['local_peak_pixel'])-evidence['evidence'][0]['local_peak_pixel'])),
        stationary_controls=controls,frames=[],
        processing=dict(geometry='Fixed ICRS tangent-plane WCS for both exposures; no target tracking or injected source.',
            background_subtraction='One spatially constant median per exposure, for display only.',
            background_levels=bg,common_display_limits=[low,high],stretch='asinh, identical in both exposures'),
        evidence=evidence,
        limitations=['Known comet example, not a new discovery or automated motion detection.',
            'Positions A/B are MOST ephemerides. Local peaks are exploratory checks, not precision astrometry.',
            'Different local wavelengths and PSFs: brightness changes cannot be interpreted as intrinsic variability.',
            'Peak/background ratios are display diagnostics, not calibrated detection significances.'],
        acknowledgement=m['acknowledgement'])
    target=Path(__file__).resolve().parents[1]/'frontend/public/motion-demo'
    target.mkdir(exist_ok=True)
    shutil.copyfile(store.ROOT/'audit'/'3iatlas-december-most.json',target/'most-response.json')
    report['most_response']='/motion-demo/most-response.json'
    for i,(f,a,e) in enumerate(zip(m['frames'],residuals,evidence['evidence'])):
        image=f'{i+1}.png'; Image.fromarray(stretch_rgba(a,low,high)[::-1]).save(target/image)
        original=f'{i+1}-original.png';shutil.copyfile(folder/(f['id']+'.png'),target/original)
        fitspath=f'{i+1}.fits';shutil.copyfile(folder/(f['id']+'.fits'),target/fitspath)
        report['frames'].append(dict(id=f['id'],date=f['date'],mjd=f['mjd'],point=e['point'],
            image='/motion-demo/'+image,original='/motion-demo/'+original,fits='/motion-demo/'+fitspath,
            archive_url=f['url'],native_fits_sha256=f['sha256'],
            displayed_fits_sha256=hashlib.sha256((target/fitspath).read_bytes()).hexdigest(),
            wavelength_um=f['wavelength_um'],bandwidth_um=f['bandwidth_um']))
    (target/'evidence.json').write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    config={k:report[k] for k in ('analysis_id','object','minutes','predicted_separation_arcmin','frames')}
    (target.parents[1]/'src/motionShowcase.json').write_text(json.dumps(config,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('analysis_id','minutes','predicted_separation_arcmin','measured_peak_separation_pixels','stationary_controls')},indent=2))


if __name__=='__main__':main()
