"""SEP/SExtractor-core source extraction following the IRSA notebook workflow.

Independent adapter, not a claim to execute the external SExtractor binary or
to identify moving objects. Runs on native images with variance and flags.
"""
import numpy as np
import sep
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS

from backend.calibrated import FIT_BAD
from backend.science import download_path

NOTEBOOK='https://caltech-ipac.github.io/irsa-tutorials/spherex-source-discovery-tool-demo/'


def extract(data,variance,mask,threshold,minarea):
    valid=~mask&np.isfinite(data)&np.isfinite(variance)&(variance>0)
    if valid.sum()<64:raise ValueError('Za mało ważnych pikseli do modelowania tła.')
    cleaned=np.ascontiguousarray(np.where(valid,data,np.median(data[valid])),dtype=np.float64)
    invalid=np.ascontiguousarray(~valid)
    background=sep.Background(cleaned,mask=invalid,bw=min(32,data.shape[1]),bh=min(32,data.shape[0]),fw=3,fh=3)
    residual=np.ascontiguousarray(cleaned-background.back())
    error=np.ascontiguousarray(np.sqrt(np.where(valid,variance,1)))
    objects=sep.extract(residual,threshold,err=error,mask=invalid,minarea=minarea,deblend_nthresh=32,deblend_cont=.005)
    return objects,dict(global_background=float(background.globalback),global_rms=float(background.globalrms),valid_fraction=float(valid.mean()))


def discover(manifest,frame_id,threshold=5,minarea=3,progress=lambda i,n:None):
    frame=next((f for f in manifest['frames'] if f['id']==frame_id),None)
    if not frame:raise ValueError('Wybierz zdjęcie tej analizy.')
    search=manifest['search'];path=download_path(frame,SkyCoord(search['ra'],search['dec'],unit='deg'),search['fov_arcmin'])
    progress(0,1)
    with fits.open(path,memmap=False) as hdus:
        data=hdus['IMAGE'].data.astype(float);variance=hdus['VARIANCE'].data.astype(float);flags=hdus['FLAGS'].data.astype(np.uint32)
        badmask=sum(1<<bit for name,bit in frame['flag_definitions'].items() if name in FIT_BAD)
        objects,metadata=extract(data,variance,(flags&badmask)!=0,threshold,minarea)
        spatial=WCS(hdus['IMAGE'].header);output=WCS(manifest['wcs'])
        candidates=[]
        for index,obj in enumerate(sorted(objects,key=lambda o:o['flux'],reverse=True)):
            coord=spatial.pixel_to_world(float(obj['x']),float(obj['y']))
            px,py=output.world_to_pixel(coord);n=manifest['pixels'];x=float((px+.5)/n);y=float(1-(py+.5)/n)
            if not 0<=x<=1 or not 0<=y<=1:continue
            candidates.append(dict(id=f'{frame_id}:{index}',point=dict(x=x,y=y),ra=float(coord.ra.deg),dec=float(coord.dec.deg),
                                   native_x=float(obj['x']),native_y=float(obj['y']),pixels=int(obj['npix']),
                                   sep_flags=int(obj['flag']),peak_surface_brightness=float(obj['peak']),
                                   unit=frame['unit']))
    return dict(kind='discovery',frame_id=frame_id,date=frame['date'],candidates=candidates[:100],
                detected_count=len(candidates),truncated=len(candidates)>100,background=metadata,
                implementation='SEP (SExtractor core), independent adapter of IRSA notebook workflow',
                source=NOTEBOOK,source_sha256=frame['sha256'],
                limitations=['Kandydaci to źródła w pojedynczym zdjęciu, nie detekcje ruchu ani nowych obiektów.',
                             'Próg ekstrakcji odnosi się do mapy wariancji; nie jest prawdopodobieństwem odkrycia.',
                             'Tło SEP i deblending są przybliżeniami. Sprawdź artefakty, sąsiadów i pozostałe daty.',
                             'Nie uruchomiono zewnętrznego programu SExtractor ani całego pakietu notebooka IRSA.'])
