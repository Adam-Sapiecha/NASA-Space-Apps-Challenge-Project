"""Bounded access to official IRSA HiPS metadata and release calibration files."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from threading import Lock
from xml.etree import ElementTree

import httpx
import numpy as np
from astropy.io import fits

from backend import store

HIPS = 'https://irsa.ipac.caltech.edu/data/hips/SPHEREx/spherex_allsky_cube'
S3 = 'https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com'
DOWNLOAD_LOCK = Lock()


def hips_metadata():
    cached = store.get('irsa_resource', 'hips-dr1')
    if cached:
        return cached
    response = httpx.get(HIPS+'/properties', timeout=25)
    response.raise_for_status()
    properties = dict(line.split('=', 1) for line in response.text.splitlines() if '=' in line and not line.lstrip().startswith('#'))
    properties = {k.strip(): v.strip() for k,v in properties.items()}
    waves = [float(v) for v in properties['data_cube_crval3_arr'].split()]
    if len(waves) != 102 or not all(np.isfinite(w) and w > 0 for w in waves):
        raise ValueError('Nieobsługiwany układ warstw SPHEREx HiPS.')
    result = dict(url=HIPS, title=properties['obs_title'], release_date=properties.get('hips_release_date'),
                  start_mjd=float(properties['t_min']), end_mjd=float(properties['t_max']),
                  first_frame=int(properties.get('hips_cube_firstframe', '1')),
                  layers=[dict(index=i, wavelength_um=w, band=i//17+1, channel=i%17+1, available=i not in (50,51)) for i,w in enumerate(waves)],
                  description=properties.get('obs_description'),
                  properties=properties,
                  limitations=['Mozaika wielu dat, nie animacja czasu ani jednoczesne widmo.',
                               'Warstwy 50 i 51 (indeks od zera) są puste.',
                               'HiPS PNG ma stałą skalę i ograniczony zakres jasności. Nie służy do fotometrii.'])
    store.put('irsa_resource', 'hips-dr1', result)
    return result


def layer_properties(index,base_url):
    metadata=hips_metadata()
    if not 0<=index<len(metadata['layers']) or not metadata['layers'][index]['available']:
        raise ValueError('Pusta lub nieznana warstwa SPHEREx.')
    properties={k:v for k,v in metadata['properties'].items() if not k.startswith(('data_cube_','hips_cube_','custom_tile_format'))}
    properties.update(dataproduct_type='image',hips_service_url=f'{base_url}/api/irsa/hips/layers/{index}',
                      obs_title=f"SPHEREx DR1 {metadata['layers'][index]['wavelength_um']:.3f} um",
                      creator_did=f'ivo://IPAC/P/SPHEREx/DR1/channel-{index}',hips_initial_fov='2')
    return '\n'.join(f'{k} = {v}' for k,v in properties.items())+'\n'


@lru_cache(maxsize=128)
def hips_tile(index,order,directory,pixel):
    if index not in range(102) or index in (50,51) or order not in range(6) or not 0<=pixel<12*4**order or directory!=pixel//10000*10000:
        raise ValueError('Niepoprawny kafelek HiPS.')
    suffix='' if index==0 else f'_{index}'
    url=f'{HIPS}/Norder{order}/Dir{directory}/Npix{pixel}/Npix{pixel}{suffix}.png'
    with httpx.stream('GET',url,timeout=25) as response:
        response.raise_for_status()
        data=bytearray()
        for chunk in response.iter_bytes():
            data.extend(chunk)
            if len(data)>2*1024*1024:raise ValueError('Kafelek HiPS przekracza limit 2 MB.')
    if not data.startswith(b'\x89PNG'):raise ValueError('Niepoprawny obraz HiPS.')
    return bytes(data)


@lru_cache(maxsize=8)
def hips_allsky(index):
    if index not in range(102) or index in (50,51):
        raise ValueError('Pusta lub nieznana warstwa SPHEREx.')
    suffix='' if index==0 else f'_{index}'
    with httpx.stream('GET',f'{HIPS}/Norder3/Allsky{suffix}.png',timeout=25) as response:
        response.raise_for_status()
        data=bytearray()
        for chunk in response.iter_bytes():
            data.extend(chunk)
            if len(data)>8*1024*1024:raise ValueError('Podgląd HiPS przekracza limit 8 MB.')
    if not data.startswith(b'\x89PNG'):raise ValueError('Niepoprawny podgląd HiPS.')
    return bytes(data)


def calibration_product(collection, kind, detector):
    """Pin a unique calibration in this release; never silently choose a newer one."""
    if collection not in ('spherex_dr1', 'spherex_qr3') or kind not in ('spectral_wcs','solid_angle_pixel_map') or detector not in range(1,7):
        raise ValueError('Nieobsługiwana kalibracja.')
    release = collection.removeprefix('spherex_')
    key = f'{release}:{kind}:D{detector}'
    pinned = store.get('calibration', key)
    if not pinned:
        response = httpx.get(S3+'/', params={'list-type':'2', 'prefix':f'{release}/{kind}/', 'max-keys':1000}, timeout=30)
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
        ns = {'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
        if root.findtext('s:IsTruncated', namespaces=ns) == 'true':
            raise ValueError('Lista kalibracji przekracza limit; wymaga jawnego wyboru wersji.')
        matches = [item.findtext('s:Key', namespaces=ns) for item in root.findall('s:Contents',ns)]
        matches = [k for k in matches if k and f'/{detector}/' in k and k.endswith('.fits') and k.startswith(f'{release}/{kind}/')]
        if len(matches) != 1:
            raise ValueError('Brak jednoznacznej wersji kalibracji tego wydania. Nie wybrano jej automatycznie.')
        pinned = dict(collection=collection, kind=kind, detector=detector, key=matches[0], url=S3+'/'+matches[0],
                      version=matches[0].split('/')[2], association='unique_product_in_release_listing')
        store.put('calibration', key, pinned)
    folder = store.ROOT/'calibrations'
    folder.mkdir(exist_ok=True)
    path = folder/(hashlib.sha256(pinned['url'].encode()).hexdigest()+'.fits')
    with DOWNLOAD_LOCK:
        if not path.exists():
            temporary = path.with_suffix('.part')
            try:
                with httpx.stream('GET', pinned['url'], timeout=90) as response:
                    response.raise_for_status()
                    count = 0
                    with temporary.open('wb') as output:
                        for chunk in response.iter_bytes():
                            count += len(chunk)
                            if count > 48*1024*1024:
                                raise ValueError('Przekroczono limit kalibracji 48 MB.')
                            output.write(chunk)
                with fits.open(temporary) as hdus:
                    if not any(hdu.data is not None for hdu in hdus):
                        raise ValueError('Kalibracja nie zawiera danych.')
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
    provenance = dict(pinned, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    return path, provenance


def parent_coordinates(header, x, y):
    if 'CRPIX1A' not in header or 'CRPIX2A' not in header:
        raise ValueError('Brak transformacji wycinka do detektora (CRPIX1A/CRPIX2A).')
    expected = {'CRVAL1A': 0., 'CRVAL2A': 0., 'CDELT1A': 1., 'CDELT2A': 1.,
                'PC1_1A': 1., 'PC2_2A': 1., 'PC1_2A': 0., 'PC2_1A': 0.}
    if any(not np.isfinite(header.get(k, v)) or not np.isclose(header.get(k, v), v, rtol=0, atol=1e-10) for k, v in expected.items()):
        raise ValueError('Nieobsługiwana rotacja, skala lub punkt odniesienia WCS-A wycinka.')
    if any(k in header for k in ('CD1_1A', 'CD1_2A', 'CD2_1A', 'CD2_2A')) or any(header.get(k, 'LINEAR').strip() != 'LINEAR' for k in ('CTYPE1A','CTYPE2A')):
        raise ValueError('Nieobsługiwana macierz lub typ WCS-A wycinka.')
    if not np.isfinite([header['CRPIX1A'], header['CRPIX2A']]).all():
        raise ValueError('Niepoprawne przesunięcie WCS-A.')
    return 1+np.asarray(x)-header['CRPIX1A'], 1+np.asarray(y)-header['CRPIX2A']


def calibration_cutout(path, extension, header, shape):
    yy, xx = np.indices(shape)
    px, py = parent_coordinates(header,xx,yy)
    # Cutout offsets are integral. Reject unknown rotations/scales instead of guessing.
    if not np.allclose(px,np.round(px),atol=1e-6,rtol=0) or not np.allclose(py,np.round(py),atol=1e-6,rtol=0):
        raise ValueError('Nieobsługiwana geometria kalibracji wycinka.')
    ix, iy = np.round(px).astype(int), np.round(py).astype(int)
    with fits.open(path, memmap=False) as hdus:
        from astropy import units as u
        if extension not in hdus or hdus[extension].data is None or hdus[extension].data.ndim != 2:
            raise ValueError('Brak wymaganego rozszerzenia kalibracji: '+extension)
        expected_unit = u.arcsec**2 if extension == 'IMAGE' else u.um
        unit = hdus[extension].header.get('BUNIT')
        if not unit or not u.Unit(unit).is_equivalent(expected_unit):
            raise ValueError('Niepoprawna jednostka mapy kalibracyjnej '+extension)
        detector = hdus[extension].header.get('DETECTOR', hdus[0].header.get('DETECTOR'))
        if detector is not None and 'DETECTOR' in header and int(detector) != int(header['DETECTOR']):
            raise ValueError('Mapa kalibracyjna innego detektora.')
        source = np.asarray(hdus[extension].data, float)*u.Unit(unit).to(expected_unit)
        output = np.full(shape,np.nan)
        valid = (ix>=0)&(iy>=0)&(ix<source.shape[1])&(iy<source.shape[0])
        output[valid] = source[iy[valid],ix[valid]]
    return output
