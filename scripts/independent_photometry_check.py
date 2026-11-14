"""Optional Photutils cross-check on real cached pixels, not detection validation.

uv pip install --python .venv/Scripts/python.exe --target .cache/validation-libs --no-deps photutils==3.1.1
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'.cache/validation-libs')]
import numpy as np
import photutils
from photutils.aperture import SkyCircularAperture, SkyCircularAnnulus, aperture_photometry
from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_area
from backend import store
from backend.science import download_path
from backend.measurements import measure


def main():
    from astropy import log
    log.setLevel('ERROR')
    five=json.loads((store.ROOT/'audit/five-targets-final.json').read_text())
    wise=next(t for t in five['targets'] if t['target']['id']=='wise0855')
    id=wise['analysis_id']
    manifest=store.get('analysis',id)
    output=dict(checked_at=datetime.now(timezone.utc).isoformat(),analysis_id=id,
                library='photutils',version=photutils.__version__,checks=[],
                limits=['Tests numerical aperture sums, background and random errors on real pixels.',
                        'Not a validation of source identity, total flux, ePSF, variability or discovery significance.',
                        'SkyCircularAperture locally approximates sky geometry; boundary pixels can differ in distorted WCS.'])
    # Explicit mask policy from IRSA documentation, independently listed here.
    rejected={'OVERFLOW','SUR_ERROR','NONFUNC','MISSING_DATA','HOT','COLD','NONLINEAR','PHANMISS','PERSIST','OUTLIER','CROSSTALK','GHOST','STREAK','BLOOM','SNOWBALL','HALO','SATELLITE_HALO','DICHROIC'}
    positions=[(s['point']['x'],s['point']['y']) for s in wise['samples'] if s['measurement']['valid']]
    positions += [(.3,.3),(.7,.7),(.3,.7),(.7,.3)]
    for x,y in positions:
        local=measure(manifest,x,y,12.4)
        coord=SkyCoord(local['ra'],local['dec'],unit='deg')
        for row in local['rows']:
            if not row['valid']:
                continue
            frame=next(f for f in manifest['frames'] if f['id']==row['id'])
            path=download_path(frame,SkyCoord(manifest['search']['ra'],manifest['search']['dec'],unit='deg'),manifest['search']['fov_arcmin'])
            with fits.open(path) as hdus:
                data=np.array(hdus['IMAGE'].data,float);var=np.array(hdus['VARIANCE'].data,float);flags=hdus['FLAGS'].data
                wcs=WCS(hdus['IMAGE'].header)
                maskword=sum(1<<bit for name,bit in frame['flag_definitions'].items() if name in rejected)
                sourceword=sum(1<<bit for name,bit in frame['flag_definitions'].items() if name=='SOURCE')
                bad=~np.isfinite(data)|~np.isfinite(var)|(var<=0)|((flags&maskword)!=0)
                ap=SkyCircularAperture(coord,12.4*u.arcsec).to_pixel(wcs)
                ann=SkyCircularAnnulus(coord,22.32*u.arcsec,37.2*u.arcsec).to_pixel(wcs)
                sky_mask=ann.to_mask(method='center').to_image(data.shape)>0
                sky_mask&=~bad&((flags&sourceword)==0)
                if sky_mask.sum()<12:
                    continue
                background=float(np.mean(data[sky_mask]))
                factor=(u.Unit(hdus['IMAGE'].header['BUNIT'])*proj_plane_pixel_area(wcs)*u.deg**2).to(u.mJy)
                summed=aperture_photometry((data-background)*factor,ap,error=np.sqrt(var)*factor,mask=bad,method='center')
                count=float(ap.area_overlap(data,mask=bad,method='center'))
                flux=float(summed['aperture_sum'][0].to_value(u.mJy))
                error=float(np.sqrt(summed['aperture_sum_err'][0]**2+(count*factor)**2*var[sky_mask].sum()/sky_mask.sum()**2).to_value(u.mJy))
                output['checks'].append(dict(point=dict(x=x,y=y),frame_id=frame['id'],source_sha256=frame['sha256'],
                    local_flux_mjy=row['flux_mjy'],photutils_flux_mjy=flux,delta_mjy=flux-row['flux_mjy'],
                    local_error_mjy=row['error_mjy'],photutils_error_mjy=error,
                    local_pixels=row['aperture_pixels'],photutils_pixels=count,background_pixels=int(sky_mask.sum())))
    if not output['checks']:
        raise RuntimeError('No valid control apertures: independent comparison is inconclusive.')
    output['max_abs_delta_mjy']=max(abs(c['delta_mjy']) for c in output['checks'])
    path=store.ROOT/'audit'/'independent-photutils.json'
    path.write_text(json.dumps(output,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps(output,indent=2))


if __name__=='__main__':
    main()
