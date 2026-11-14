"""Shared numerical definitions; no I/O or automatic scientific inference."""
import numpy as np
from scipy.ndimage import map_coordinates


def weighted_fit(matrix, values, noise):
    matrix, noise = np.asarray(matrix,float), np.asarray(noise,float)
    design = matrix/noise[:, None]
    rhs = np.asarray(values)/noise
    if not np.isfinite(design).all() or not np.isfinite(rhs).all() or np.any(noise <= 0):
        raise ValueError('Niepoprawne dane lub wariancja dopasowania.')
    left, singular, right = np.linalg.svd(design, full_matrices=False)
    if len(singular) < matrix.shape[1] or singular[-1] <= 0 or singular[0]/singular[-1] > 1e8:
        raise ValueError('Niestabilne dopasowanie modelu i tła.')
    beta = right.T @ ((left.T @ rhs)/singular)
    covariance = (right.T/singular**2) @ right
    return beta, covariance, float(singular[0]/singular[-1])


def epsf_profile(shape, x, y, epsf, ox, oy):
    """Evaluate pixel-convolved ePSF; normalize its complete native support.

    The normalization grid is independent of masks and cropped data boundaries.
    Flux means the supplied finite model, not an extrapolated infinite PSF.
    """
    if min(ox, oy) < 1 or epsf.ndim != 2 or not np.isfinite(epsf).all():
        raise ValueError('Niepoprawny model ePSF.')
    hx, hy = (epsf.shape[1]-1)/2, (epsf.shape[0]-1)/2
    def evaluate(xx, yy):
        return map_coordinates(epsf, [(yy-y)*oy+hy, (xx-x)*ox+hx], order=3, mode='constant', cval=0)
    gy, gx = np.mgrid[int(np.ceil(y-hy/oy)):int(np.floor(y+hy/oy))+1,
                      int(np.ceil(x-hx/ox)):int(np.floor(x+hx/ox))+1]
    normalization = float(evaluate(gx, gy).sum())
    if not np.isfinite(normalization) or normalization <= 0:
        raise ValueError('Niepoprawna normalizacja próbkowanego ePSF.')
    yy, xx = np.indices(shape)
    return evaluate(xx, yy)/normalization


def plane_aperture(data, variance, source, background, factor, x, y):
    yy, xx = np.indices(data.shape)
    dx, dy = xx-x, yy-y
    matrix = np.column_stack([np.ones(background.sum()), dx[background], dy[background]])
    beta, covariance, condition = weighted_fit(matrix, data[background], np.sqrt(variance[background]))
    integral = np.array([factor[source].sum(), np.sum(factor[source]*dx[source]), np.sum(factor[source]*dy[source])])
    flux = np.sum(factor[source]*data[source])-integral@beta
    var = np.sum(factor[source]**2*variance[source])+integral@covariance@integral
    return dict(flux_mjy=float(flux), error_mjy=float(np.sqrt(var)), background=float(beta[0]),
                background_dx=float(beta[1]), background_dy=float(beta[2]), condition_number=condition)
