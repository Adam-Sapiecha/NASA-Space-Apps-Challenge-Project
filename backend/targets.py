"""Frozen catalogue identities and approximate positions, never image detections."""
import json
from pathlib import Path

from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time

TARGETS = json.loads(Path(__file__).with_name('targets.json').read_text(encoding='utf-8'))


def position(target, mjd):
    coord = SkyCoord(target['ra_deg'] * u.deg, target['dec_deg'] * u.deg,
                     pm_ra_cosdec=target['pmra_masyr'] * u.mas/u.yr,
                     pm_dec=target['pmdec_masyr'] * u.mas/u.yr,
                     obstime=Time(target['epoch_mjd'], format='mjd'), frame='icrs')
    # No distance/RV means no claimed perspective acceleration or apparent place.
    moved = coord.apply_space_motion(new_obstime=Time(mjd, format='mjd'))
    return dict(ra=float(moved.ra.deg), dec=float(moved.dec.deg), mjd=float(mjd))


def target_fields(mjd=61041.0):
    return [dict(**target, position=position(target, mjd),
                 limitations=['Catalogue prediction, not identification in SPHEREx.',
                              'Proper motion only; no parallax, orbital or observer correction.'])
            for target in TARGETS]
