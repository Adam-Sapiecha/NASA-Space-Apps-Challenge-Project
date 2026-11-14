"""Gaia context from VizieR; linear proper motion, never an apparent position."""
import hashlib
import warnings
from datetime import datetime, timezone

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from astroquery.vizier import Vizier

from backend import store


def gaia(ra, dec, radius_arcmin, mjd):
    key = hashlib.sha256(f'gaia-dr3-v2:{ra}:{dec}:{radius_arcmin}:{mjd}'.encode()).hexdigest()
    cached = store.get('catalog', key)
    if cached:
        return cached
    # CDS main service can be unavailable; use its documented HTTPS mirrors.
    for server in ('vizier.cfa.harvard.edu', 'vizier.idia.ac.za'):
        client = Vizier(columns=['Source', 'RA_ICRS', 'DE_ICRS', 'pmRA', 'pmDE', 'Gmag'],
                        row_limit=500, timeout=15, vizier_server=server)
        try:
            tables = client.query_region(SkyCoord(ra, dec, unit='deg'), radius=radius_arcmin*u.arcmin, catalog='I/355/gaiadr3')
            break
        except Exception:
            if server == 'vizier.idia.ac.za':
                raise
    sources = []
    if len(tables):
        for row in tables[0]:
            r, d = float(row['RA_ICRS']), float(row['DE_ICRS'])
            propagated = not np.ma.is_masked(row['pmRA']) and not np.ma.is_masked(row['pmDE']) and np.isfinite(float(row['pmRA'])) and np.isfinite(float(row['pmDE']))
            if propagated:
                coord = SkyCoord(r*u.deg, d*u.deg, pm_ra_cosdec=float(row['pmRA'])*u.mas/u.yr,
                                 pm_dec=float(row['pmDE'])*u.mas/u.yr, obstime=Time(2016, format='jyear'))
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    coord = coord.apply_space_motion(new_obstime=Time(mjd, format='mjd'))
                r, d = float(coord.ra.deg), float(coord.dec.deg)
            def optional(name):
                if name not in row.colnames or np.ma.is_masked(row[name]): return None
                value = float(row[name])
                return value if np.isfinite(value) else None
            sources.append(dict(id=str(row['Source']), ra=r, dec=d, propagated=bool(propagated),
                                reference_ra=float(row['RA_ICRS']), reference_dec=float(row['DE_ICRS']),
                                reference_epoch=2016.0, pmra=optional('pmRA'), pmdec=optional('pmDE'),
                                gmag=optional('Gmag')))
    result = dict(id=key, catalog='Gaia DR3 / VizieR I/355/gaiadr3', service=server, reference_epoch=2016.0,
                  target_mjd=mjd, retrieved_at=datetime.now(timezone.utc).isoformat(), sources=sources,
                  truncated=len(sources)>=500, query_radius_arcmin=radius_arcmin,
                  limitations=['Prosta propagacja ruchu własnego; bez paralaksy, prędkości radialnej i pozycji pozornej.',
                               'Źródła bez ruchu własnego pozostają w epoce 2016.0.',
                               'Wyszukiwanie wokół pozycji katalogowych; szybkie źródło mogło wejść do pola spoza promienia.',
                               'Brak źródła Gaia nie dowodzi odkrycia. Kontekst optyczny różni się od podczerwieni SPHEREx.'])
    store.put('catalog', key, result)
    return result
