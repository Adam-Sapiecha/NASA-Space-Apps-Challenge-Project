"""Local, fixed-position fits using release calibrations and the supplied ePSF.

This independent implementation is not IRSA's Tractor service. It reports random
errors and residuals, and retains explicit caveats for neighbors and systematics.
"""
import hashlib
import json
import httpx

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.wcs import WCS
from scipy.ndimage import map_coordinates

from backend import store
from backend.irsa_resources import calibration_product, calibration_cutout, parent_coordinates
from backend.science import BAD_FLAGS, download_path
from backend.measurements import PHOTOMETRY_BAD_FLAGS
from backend.measurements import aperture
from backend.coordinates import point_sky
from backend.photometry_math import epsf_profile, weighted_fit, plane_aperture

FIT_BAD = PHOTOMETRY_BAD_FLAGS
METHOD = 'release-maps-epsf-2'


def require_current_report(report):
    if report.get('method') != METHOD:
        raise ValueError('Archiwalna metoda fotometrii. Wykonaj nowy pomiar z kalibracją przed dalszą analizą.')


def psf_at(hdus, x, y):
    if 'EPSF' not in hdus:
        raise ValueError('Brak nowego modelu ePSF. Stary PSF nie jest używany jako zamiennik.')
    table, header = hdus['EPSF'].data, hdus['EPSF'].header
    if str(header.get('DETCOORD', 'sky')).strip().lower() != 'sky':
        raise ValueError('Nieobsługiwana orientacja ePSF; wymagane DETCOORD=sky.')
    px, py = parent_coordinates(hdus['IMAGE'].header,x,y)
    index = int(np.argmin((table['XCENTER']-px)**2+(table['YCENTER']-py)**2))
    row = table[index]
    image = np.asarray(row['EPSF'],float)
    ox, oy = int(header['OVSMPX']),int(header['OVSMPY'])
    if image.ndim != 2 or not np.isfinite(image).all() or image.sum() <= 0 or min(ox,oy) < 1:
        raise ValueError('Niepoprawny model ePSF.')
    return image, dict(row=index,bin_x=int(row['BINX']),bin_y=int(row['BINY']),
                       parent_x=float(px),parent_y=float(py),oversample_x=ox,oversample_y=oy,
                       wavelength_zone_um=float(row['CWAVE']),bandwidth_zone_um=float(row['CBAND']),
                       stars=int(row['NSTAR']), normalization='unit_sum_native_full_model_support')


def fit_epsf(data, variance, valid, pixel_factor, x, y, epsf, ox, oy):
    yy,xx = np.indices(data.shape)
    dx,dy = xx-x,yy-y
    profile = epsf_profile(data.shape, x, y, epsf, ox, oy)
    region = dx**2+dy**2 <= 4.5**2
    good = region & valid & np.isfinite(pixel_factor) & (pixel_factor>0) & np.isfinite(data) & np.isfinite(variance) & (variance>0)
    if good.sum()<16 or np.sum(profile[good]) < .7:
        raise ValueError('Za mało ważnych pikseli modelu ePSF lub niepełne pokrycie źródła.')
    # Flux in mJy plus a surface-brightness background plane. No recentering.
    matrix = np.column_stack([profile[good],pixel_factor[good],pixel_factor[good]*dx[good],pixel_factor[good]*dy[good]])
    values = data[good]*pixel_factor[good]
    noise = np.sqrt(variance[good])*pixel_factor[good]
    beta,covariance,condition = weighted_fit(matrix,values,noise)
    residual = (values-matrix@beta)/noise
    return dict(flux_mjy=float(beta[0]),error_mjy=float(np.sqrt(covariance[0,0])),
                reduced_chi2=float(np.sum(residual**2)/(len(values)-4)),
                mean_abs_residual_noise=float(np.mean(np.abs(residual))),fit_pixels=int(good.sum()),
                degrees_of_freedom=int(good.sum()-4),condition_number=condition,model_fraction_covered=float(profile[good].sum()),
                background=float(beta[1]),background_dx=float(beta[2]),background_dy=float(beta[3]))


def calibrated_report(manifest,x,y,radius_arcsec,progress=lambda i,n:None):
    coord = point_sky(manifest,dict(x=x,y=y))
    search = manifest['search']; center=SkyCoord(search['ra'],search['dec'],unit='deg')
    rows,provenance = [],{}
    for i,frame in enumerate(manifest['frames']):
        progress(i,len(manifest['frames']))
        row = dict(id=frame['id'],obs_id=frame['obs_id'],band=frame['band'],date=frame['date'],mjd=frame['mjd'])
        try:
            path = download_path(frame,center,search['fov_arcmin'])
            if not path.exists(): raise ValueError('Brak natywnego FITS w cache.')
            with fits.open(path,memmap=False) as hdus:
                header=hdus['IMAGE'].header; detector=int(header['DETECTOR'])
                data=hdus['IMAGE'].data.astype(float); variance=hdus['VARIANCE'].data.astype(float); flags=hdus['FLAGS'].data.astype(np.uint32)
                spatial=WCS(header); sx,sy=map(float,spatial.world_to_pixel(coord))
                if not np.isfinite([sx,sy]).all() or not (0<=sx<data.shape[1] and 0<=sy<data.shape[0]):
                    raise ValueError('Punkt poza natywnym wycinkiem.')
                scale=float(np.sqrt(abs(np.linalg.det(spatial.pixel_scale_matrix))))*3600
                aperture_edge = min(sx,sy,data.shape[1]-1-sx,data.shape[0]-1-sy)<radius_arcsec*3/scale+1
                swcs,wp=calibration_product(search['collection'],'spectral_wcs',detector)
                area,ap=calibration_product(search['collection'],'solid_angle_pixel_map',detector)
                for p in (wp,ap):provenance[p['sha256']]=p
                wavelength=calibration_cutout(swcs,'CWAVE',header,data.shape)
                bandwidth=calibration_cutout(swcs,'CBAND',header,data.shape)
                solid_angle=calibration_cutout(area,'IMAGE',header,data.shape)
                local_wl=float(map_coordinates(wavelength,[[sy],[sx]],order=1)[0]); local_bw=float(map_coordinates(bandwidth,[[sy],[sx]],order=1)[0])
                approximate=WCS(header,fobj=hdus,key='W');approximate.sip=None
                approx_wl,approx_bw=approximate.pixel_to_world(sx,sy)
                if not np.isfinite([local_wl,local_bw]).all() or local_bw<=0 or abs(local_wl-float(approx_wl.to_value(u.um)))>max(.003,local_bw*.15) or abs(local_bw-float(approx_bw.to_value(u.um)))>max(.003,local_bw*.15):
                    raise ValueError('Mapa kalibracyjna nie zgadza się z geometrią WCS-WAVE; nie zastosowano jej.')
                factor=(u.Unit(header['BUNIT'])*u.arcsec**2).to(u.mJy)*solid_angle
                badmask=sum(1<<bit for name,bit in frame['flag_definitions'].items() if name in FIT_BAD)
                valid=np.isfinite(data)&np.isfinite(variance)&(variance>0)&((flags&badmask)==0)&np.isfinite(factor)&(factor>0)
                yy,xx=np.indices(data.shape);distance=spatial.pixel_to_world(xx,yy).separation(coord).arcsec
                source=distance<=radius_arcsec
                background_mask=sum(1<<bit for name,bit in frame['flag_definitions'].items() if name=='SOURCE')
                bg=(distance>=1.8*radius_arcsec)&(distance<=3*radius_arcsec)&valid&((flags&background_mask)==0)
                ap_result, fitted, psf_info = {}, {}, {}
                try:
                    if aperture_edge:
                        raise ValueError('Pierścień tła wykracza poza wycinek FITS.')
                    ap_result = dict(valid=True, **aperture(data,variance,flags,badmask,distance,radius_arcsec,background_mask,factor))
                except ValueError as exc:
                    ap_result = dict(valid=False,reason=str(exc))
                if ap_result.get('valid'):
                    try:
                        ap_result['plane_background'] = plane_aperture(data,variance,source,bg,factor,sx,sy)
                    except ValueError as exc:
                        ap_result['plane_background'] = dict(reason=str(exc))
                sensitivity = []
                try:
                    epsf,psf_info=psf_at(hdus,sx,sy)
                    fitted=fit_epsf(data,variance,valid,factor,sx,sy,epsf,psf_info['oversample_x'],psf_info['oversample_y'])
                    fitted['valid'] = fitted['reduced_chi2'] <= 3
                    if not fitted['valid']:
                        fitted['reason'] = 'Słaba zgodność modelu ePSF (χ²/dof > 3); nie używaj do dalszego wnioskowania.'
                    for dx,dy in [(-.5,0),(.5,0),(0,-.5),(0,.5)]:
                        try:
                            model,zone=psf_at(hdus,sx+dx,sy+dy)
                            shifted=fit_epsf(data,variance,valid,factor,sx+dx,sy+dy,model,zone['oversample_x'],zone['oversample_y'])
                            sensitivity.append(dict(dx_pixels=dx,dy_pixels=dy,**shifted))
                        except ValueError as exc:
                            sensitivity.append(dict(dx_pixels=dx,dy_pixels=dy,reason=str(exc)))
                except ValueError as exc:
                    fitted=dict(valid=False,reason=str(exc))
                row.update(valid=bool(fitted.get('valid')),wavelength_um=local_wl,bandwidth_um=local_bw,
                           aperture=ap_result,aperture_flux_mjy=ap_result.get('flux_mjy'),aperture_error_mjy=ap_result.get('error_mjy'),epsf=fitted,psf=psf_info,
                           source_sha256=frame['sha256'],source_pipeline=str(hdus[0].header.get('VERSION','unknown')),
                           position=dict(ra=float(coord.ra.deg),dec=float(coord.dec.deg),native_x=sx,native_y=sy,method='fixed-continuous-sky-position'),
                           position_sensitivity=sensitivity,neighbor_warning=ap_result.get('neighbor_warning',True),
                           background_pixels=int(bg.sum()),flags_word=int(np.bitwise_or.reduce(flags[source])) if source.any() else 0,
                           calibration_sources=[wp['sha256'],ap['sha256']])
                if not row['valid']:
                    row['reason'] = fitted.get('reason','Brak ważnego dopasowania ePSF.')
                # This is model sensitivity on the same pixels, not independent errors.
                variants=[v['flux_mjy'] for v in sensitivity if 'flux_mjy' in v]
                if 'flux_mjy' in fitted:
                    variants.append(fitted['flux_mjy'])
                row['robustness'] = dict(status='requires_validation',
                    epsf_position_range_mjy=[min(variants),max(variants)] if variants else None,
                    aperture_minus_epsf_mjy=ap_result['flux_mjy']-fitted['flux_mjy'] if ap_result.get('valid') and 'flux_mjy' in fitted else None,
                    background_model_delta_mjy=ap_result['plane_background']['flux_mjy']-ap_result['flux_mjy'] if ap_result.get('valid') and 'flux_mjy' in ap_result['plane_background'] else None,
                    interpretation='Warianty tych samych danych: bez wyboru najlepszego strumienia i bez testu istotności.')
        except (ValueError,KeyError,OSError,httpx.HTTPError) as exc:
            row.update(valid=False,reason=str(exc))
        rows.append(row)
    return dict(kind='calibrated',analysis_id=manifest['id'],point=dict(x=x,y=y),ra=float(coord.ra.deg),dec=float(coord.dec.deg),
                radius_arcsec=radius_arcsec,rows=rows,calibrations=list(provenance.values()),method=METHOD,
                limitations=['Lokalne dopasowanie ePSF i płaszczyzny tła nie jest usługą IRSA Tractor ani potwierdzeniem zmienności.',
                             'Błędy losowe zakładają niezależne piksele. Nie obejmują systematyki i niepewności kalibracji.',
                             'Stała pozycja ICRS; brak dopasowania sąsiadów i automatycznego śledzenia ruchu.',
                             'Apertura i ePSF mają osobną ważność. Rozrzut przy przesunięciach ±0,5 piksela i zmianie tła jest diagnostyką modelu, nie błędem losowym.',
                             'Kalibracje przypięto z jednoznacznej listy wydania; zgodność konkretnego produktu należy kontrolować przy zmianie wydania.',
                             'Strumień ePSF dotyczy dostarczonego modelu o skończonym zasięgu. Wyniki wymagają porównania z oficjalną spektrofotometrią.'])
