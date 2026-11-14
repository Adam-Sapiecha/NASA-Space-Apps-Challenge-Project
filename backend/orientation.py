"""Fast, offline field geometry and terrestrial orientation; no FITS downloads."""
import warnings
from datetime import datetime, timezone

import numpy as np
from astropy import units as u
from astropy.coordinates import AltAz, EarthLocation, SkyCoord
from astropy.time import Time
from astropy.utils import iers
from astropy.wcs import WCS

iers.conf.auto_download = False
iers.conf.auto_max_age = None
iers.conf.iers_degraded_accuracy = "warn"


def footprint(wcs, pixels):
    """Sample all four pixel edges (not centers), including TAN curvature."""
    w = WCS(wcs) if isinstance(wcs, dict) else wcs
    edge = np.linspace(-.5, pixels-.5, 17)
    x = np.concatenate([edge, np.full(17, pixels-.5), edge[::-1], np.full(17, -.5)])
    y = np.concatenate([np.full(17, -.5), edge, np.full(17, pixels-.5), edge[::-1]])
    sky = w.pixel_to_world(x, y)
    return np.column_stack([sky.ra.deg, sky.dec.deg]).tolist()


def direction(ra, dec, latitude, longitude, height_m=0, utc=None):
    time = Time(utc or datetime.now(timezone.utc))
    if not time.isscalar or not np.isfinite(time.mjd) or not 15020 <= time.mjd <= 88434:
        raise ValueError("Czas musi należeć do lat 1900–2100.")
    location = EarthLocation.from_geodetic(longitude*u.deg, latitude*u.deg, height_m*u.m)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        altaz = SkyCoord(ra, dec, unit="deg", frame="icrs").transform_to(
            AltAz(obstime=time, location=location, pressure=0*u.hPa))
        table = iers.earth_orientation_table.get()
        _, status = table.ut1_utc(time, return_status=True)
    altitude = float(altaz.alt.deg)
    limited = bool(status < 0 or caught)
    return dict(utc=time.utc.isot+"Z", altitude_deg=altitude,
                azimuth_deg=None if abs(altitude) > 89.9 else float(altaz.az.deg),
                above_horizon=altitude >= 0, refraction=False,
                accuracy="limited" if limited else "bundled_iers",
                notes=["Kierunek pola ICRS z miejsca na Ziemi; bez modelu ruchu źródła i bez refrakcji.",
                       "Nad horyzontem nie oznacza widoczności. To nie jest pozycja satelity SPHEREx.",
                       "Użyto lokalnej tabeli IERS; brak aktualizacji sieciowej." +
                       (" Data poza zakresem lub ostrzeżenie transformacji: dokładność ograniczona." if limited else "")])
