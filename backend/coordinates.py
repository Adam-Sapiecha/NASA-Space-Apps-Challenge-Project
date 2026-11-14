"""One continuous sky-position convention for clicks, measurements and exports."""
import numpy as np
from astropy.wcs import WCS


def point_pixels(manifest, point):
    n = manifest['pixels']
    x, y = float(point['x']), float(point['y'])
    if not np.isfinite([x, y]).all() or not (0 <= x <= 1 and 0 <= y <= 1):
        raise ValueError('Punkt musi leżeć na obrazie.')
    return x*n-.5, (1-y)*n-.5


def point_sky(manifest, point):
    return WCS(manifest['wcs']).pixel_to_world(*point_pixels(manifest, point))


def point_sample(manifest, point, arrays):
    """Interpolate browsing wavelengths at the click; flags refer to its pixel.

    No interpolation through missing values. Half-pixel outer borders have no
    wavelength sample rather than silently clamping to a different position.
    """
    x, y = point_pixels(manifest, point)
    n = manifest['pixels']
    ix = min(n-1, int(point['x']*n))
    iy = n-1-min(n-1, int(point['y']*n))
    def interpolate(array):
        if not (0 <= x <= n-1 and 0 <= y <= n-1):
            return None
        x0, y0 = int(np.floor(x)), int(np.floor(y))
        total = 0.
        for px, wx in [(x0, 1-(x-x0)), (min(x0+1, n-1), x-x0)]:
            for py, wy in [(y0, 1-(y-y0)), (min(y0+1, n-1), y-y0)]:
                weight = wx*wy
                if weight == 0:
                    continue
                value = float(array[py, px])
                if not np.isfinite(value):
                    return None
                total += weight*value
        return float(total)
    return dict(wavelength_um=interpolate(arrays['wavelength']),
                bandwidth_um=interpolate(arrays['bandwidth']),
                valid=bool(arrays['valid'][iy, ix]), flags_word=int(arrays['flags'][iy, ix]),
                pixel=dict(x=ix, y=iy))


def frame_point(note, frame):
    if note.get('mode') != 'route':
        return note.get('point')
    anchors = note.get('anchors') or []
    anchor = next((a for a in anchors if a['frameId'] == frame['id']), None)
    if anchor:
        return dict(x=anchor['x'], y=anchor['y'])
    if len(anchors) == 2 and anchors[0]['mjd'] != anchors[1]['mjd']:
        a, b = anchors
        t = (frame['mjd']-a['mjd'])/(b['mjd']-a['mjd'])
        p = dict(x=a['x']+t*(b['x']-a['x']), y=a['y']+t*(b['y']-a['y']))
        if 0 <= p['x'] <= 1 and 0 <= p['y'] <= 1:
            return p
    return None
