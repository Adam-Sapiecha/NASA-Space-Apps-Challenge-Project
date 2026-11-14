"""Run the automatic pipeline and export reproducible real-image prediction data."""
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from astropy.io import fits
from PIL import Image
from backend import store
from backend.auto_motion import automatic_prediction
from backend.science import stretch_rgba
from prepare_prediction_demo import IDENT


def main():
    m=store.get('analysis',IDENT)
    if not m:raise ValueError('Run prepare_prediction_demo.py first.')
    result=automatic_prediction(m)
    if result['status']!='ready':raise ValueError(str(result.get('reason',result['status'])))
    root=Path(__file__).resolve().parents[1]
    target=root/'frontend/public/prediction-demo';target.mkdir(exist_ok=True)
    arrays=[fits.getdata(store.ROOT/'analyses'/IDENT/(f['id']+'.fits')).astype(float) for f in m['frames']]
    backgrounds=[float(np.nanmedian(a)) for a in arrays]
    display=[a-bg for a,bg in zip(arrays,backgrounds)]
    values=np.concatenate([a[np.isfinite(a)] for a in display]);low,high=map(float,np.percentile(values,[1,99.9]))
    for i,(frame,array) in enumerate(zip(result['frames'],display)):
        Image.fromarray(stretch_rgba(array,low,high)[::-1]).save(target/f'{i+1}.png')
        src=store.ROOT/'analyses'/IDENT/(frame['id']+'.fits')
        shutil.copyfile(src,target/f'{i+1}.fits')
        meta=m['frames'][i]
        frame.update(image=f'/prediction-demo/{i+1}.png',fits=f'/prediction-demo/{i+1}.fits',
            archive_url=meta['url'],native_sha256=meta['sha256'],
            displayed_fits_sha256=hashlib.sha256(src.read_bytes()).hexdigest())
    result.update(portable_example=True,image_pixels=m['pixels'],field_arcmin=m['search']['fov_arcmin'],wcs=m['wcs'],
        display_processing=dict(background='Separate spatially constant median per exposure, display only.',
            background_levels=backgrounds,common_limits=[low,high],geometry='Identical celestial WCS; sources are never shifted.'),
        association_reference=m['motion_target'],acknowledgement=m['acknowledgement'])
    (target/'report.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(dict(status=result['status'],analysis_id=IDENT,error_arcsec=result['validation']['error_arcsec'],
        error_pixels=result['validation']['error_pixels'],future_model_chi2=result['future_model']['reduced_chi2'])),flush=True)


if __name__=='__main__':main()
