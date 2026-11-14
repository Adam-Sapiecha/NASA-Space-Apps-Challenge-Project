"""Bounded real-image check of 3I/ATLAS using the saved official MOST response.

No source or motion is injected. Predictions and pixel evidence stay separate.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from backend import store
from backend.science import build_analysis


def main():
    if '--august' not in sys.argv:
        path = store.ROOT/'audit'/'3iatlas-december-most.json'
        path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists():
            from backend.moving_objects import search_moving
            path.write_text(json.dumps(search_moving('3I','2025-12-14','2025-12-15'),indent=2),encoding='utf-8')
        source = json.loads(path.read_text())
        rows = [r for r in source['rows'] if r['productid']=='D6' and r['observationid'] in
                ('2025W50_2A_0741_2', '2025W50_2A_0755_2')]
        ra = float(np.mean([r['ra_obj'] for r in rows]))
        dec = float(np.mean([r['dec_obj'] for r in rows]))
        observations = []
        for r in rows:
            url = 'https://irsa.ipac.caltech.edu/'+r['uri']
            observations.append(dict(id=hashlib.sha256(url.encode()).hexdigest()[:20],
                obs_id=r['observationid'],url=url,mjd=(r['mjd_start']+r['mjd_end'])/2,
                date=r['start_date'].replace(' ','T'),band='SPHEREx-D6',collection='spherex_dr1',
                em_min_um=4.4115,em_max_um=5.0096))
        if len(observations) != 2:
            raise ValueError(f'Expected two matching DR1 visits, found {len(observations)}.')
        ident = 'motion3iatlas20251214d6'
        search = dict(id=ident,ra=ra,dec=dec,fov_arcmin=12,collection='spherex_dr1',observations=observations,
            note='Products selected from the official MOST result for 3I, December 14.')
        source['source_path'] = path
    else:
        return august()
    finish(ident, search, observations, rows, source)


def august():
    source = json.loads((store.ROOT / 'smoke_most.json').read_text())
    rows = [r for r in source['rows'] if r['productid'] == 'D6' and
            (r['start_date'].startswith('2025-08-07 02:32') or
             r['start_date'].startswith('2025-08-07 05:51'))]
    if len(rows) != 2:
        raise ValueError('Expected the two recorded MOST visits, refusing substitutions.')
    observations = []
    for r in rows:
        url = 'https://irsa.ipac.caltech.edu/' + r['uri']
        observations.append(dict(id=hashlib.sha256(url.encode()).hexdigest()[:20],
            obs_id=r['observationid'], url=url, mjd=(r['mjd_start']+r['mjd_end'])/2,
            date=r['start_date'].replace(' ', 'T'), band='SPHEREx-D6',
            collection='spherex_dr1', em_min_um=4.4115, em_max_um=5.0096))
    ra = float(np.mean([r['ra_obj'] for r in rows]))
    dec = float(np.mean([r['dec_obj'] for r in rows]))
    ident = 'motion3iatlas20250807d6'
    search = dict(id=ident, ra=ra, dec=dec, fov_arcmin=12, collection='spherex_dr1',
        observations=observations, retrieved_at=source.get('retrieved_at'),
        note='Products selected from the saved official MOST result for 3I.',
        most_source=source['source'])
    source['source_path'] = store.ROOT/'smoke_most.json'
    finish(ident, search, observations, rows, source)


def finish(ident, search, observations, rows, source):
    if not store.get('analysis', ident):
        store.put('search', ident, search)
        build_analysis(ident, search, [o['id'] for o in observations])
    manifest = store.get('analysis', ident)
    if not manifest or len(manifest['frames']) != 2:
        raise RuntimeError(str(store.get('job', ident)))
    # Detector-wide bounds from IRSA's official observation table, not the
    # narrower local WCS-WAVE value measured independently for each exposure.
    manifest['search']=search
    for frame in manifest['frames']:
        frame.update(em_min_um=4.4115,em_max_um=5.0096)
    (store.ROOT/'analyses'/ident/'manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False),encoding='utf-8')
    store.put('analysis',ident,manifest)
    store.put('search',ident,search)
    w = WCS(manifest['wcs'])
    evidence = []
    for r, o in zip(rows, observations):
        frame = next(f for f in manifest['frames'] if f['id'] == o['id'])
        x, y = w.world_to_pixel(SkyCoord(r['ra_obj'], r['dec_obj'], unit='deg'))
        a = fits.getdata(store.ROOT / 'analyses' / ident / (o['id']+'.fits'))
        yy, xx = np.indices(a.shape)
        d = np.hypot(xx-x, yy-y)
        near = np.where(d <= 3, a, np.nan)
        py, px = np.unravel_index(np.nanargmax(near), a.shape)
        bg = a[(d >= 5) & (d <= 10) & np.isfinite(a)]
        median = float(np.median(bg))
        noise = float(1.4826*np.median(np.abs(bg-median)))
        evidence.append(dict(frame_id=o['id'], date=o['date'], prediction_ra=r['ra_obj'],
            prediction_dec=r['dec_obj'], point=dict(x=(float(x)+.5)/len(a),y=1-(float(y)+.5)/len(a)),
            predicted_pixel=[float(x),float(y)], local_peak_pixel=[int(px),int(py)],
            peak_above_local_background=float(a[py,px]-median), local_background_mad=noise,
            peak_offset_pixels=float(np.hypot(px-x,py-y)), wavelength_um=frame['wavelength_um'],
            bandwidth_um=frame['bandwidth_um']))
    report = dict(analysis_id=ident, object='3I/ATLAS', evidence=evidence,
        source=source['source'], source_file_sha256=hashlib.sha256(source['source_path'].read_bytes()).hexdigest(),
        limitations=['MOST positions are predictions, not centroid measurements.',
            'Local peak is a diagnostic, not a detection significance or identity confirmation.',
            'Images use a fixed celestial WCS, without following the predicted comet.',
            'Bands, background, PSF and stationary sources must be checked before claiming motion.'])
    out = store.ROOT/'audit'/f'{ident}-candidate.json'
    out.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
