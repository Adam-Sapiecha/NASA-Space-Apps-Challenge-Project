"""IRSA SIA adapter. All URLs originate in an archive query, never user input."""
import hashlib
import math
from datetime import datetime, timezone
from urllib.parse import urlparse

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from astroquery.ipac.irsa import Irsa
import requests
from pyvo.dal import SIA2Service

COLLECTIONS = ("spherex_dr1", "spherex_qr3")


class ArchiveSession(requests.Session):
    def request(self, method, url, **kwargs):
        # PyVO uses requests directly, so Irsa.TIMEOUT does not bound this call.
        kwargs['timeout'] = (5, 20)
        return super().request(method, url, **kwargs)


def query_images(**kwargs):
    with ArchiveSession() as session:
        # The archive endpoint is already known. Avoid an additional capabilities
        # request which can stall before the actual image search starts.
        return SIA2Service(Irsa.sia_url, session=session, check_baseurl=False).search(**kwargs).to_table()

def coordinates(ra: str, dec: str):
    try:
        try:
            r, d = float(ra), float(dec)
            if not (math.isfinite(r) and math.isfinite(d) and 0 <= r < 360 and -90 <= d <= 90):
                raise ValueError("RA: 0–360°, Dec: −90–90°.")
            return SkyCoord(r, d, unit="deg", frame="icrs")
        except ValueError:
            if not any(c in ra for c in (":", "h", " ")):
                raise
            return SkyCoord(ra, dec, unit=(u.hourangle, u.deg), frame="icrs")
    except Exception as exc:
        raise ValueError("Niepoprawne współrzędne. Użyj stopni lub RA hh:mm:ss i Dec ±dd:mm:ss.") from exc

def safe_archive_url(url):
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "irsa.ipac.caltech.edu" or not parsed.path.startswith("/ibe/data/spherex/"):
        raise ValueError("Nieobsługiwany adres produktu archiwalnego.")
    return url

def search(ra, dec, fov_arcmin, collection):
    coord = coordinates(ra, dec)
    # Circumscribed circle includes the corners of the square output field.
    result = query_images(pos=(coord, fov_arcmin / 2 * math.sqrt(2) * u.arcmin), collection=[collection])
    table = result.to_table() if hasattr(result, "to_table") else result
    observations = []
    seen = set()
    for row in table:
        url = str(row["access_url"])
        try:
            safe_archive_url(url)
        except ValueError:
            continue
        key = str(row["obs_id"])
        # OBSID is shared by simultaneous detector images. Deduplicate products,
        # not OBSID, or five of the six detectors can disappear.
        if url in seen:
            continue
        seen.add(url)
        start, end = float(row["t_min"]), float(row["t_max"])
        if not (math.isfinite(start) and math.isfinite(end)):
            continue
        observations.append(dict(
            id=hashlib.sha256(url.encode()).hexdigest()[:20], obs_id=key, url=url,
            mjd=(start+end)/2, date=Time((start+end)/2, format="mjd").isot,
            start_mjd=start, end_mjd=end,
            band=str(row["energy_bandpassname"]), collection=collection,
            em_min_um=float(row["em_min"])*1e6, em_max_um=float(row["em_max"])*1e6,
        ))
    observations.sort(key=lambda x: x["mjd"])
    return dict(ra=coord.ra.deg, dec=coord.dec.deg, fov_arcmin=fov_arcmin, collection=collection,
                retrieved_at=datetime.now(timezone.utc).isoformat(), observations=observations,
                archive_rows=len(table), note="Pozycje obiektów testowych są punktami startowymi; nie zastosowano propagacji ruchu własnego.")
