"""Read actual archive coverage. No simulated observations."""
import json
import time
import sys
from pathlib import Path

from astropy import units as u
from astropy.coordinates import SkyCoord
from astroquery.ipac.irsa import Irsa
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.targets import TARGETS as CATALOGUE_TARGETS

TARGETS = [(t['name'],t['field_ra'],t['field_dec']) for t in CATALOGUE_TARGETS]

def main():
    Irsa.TIMEOUT = 90
    output = Path("data/audit")
    output.mkdir(parents=True, exist_ok=True)
    report = []
    for name, ra, dec in TARGETS:
        started = time.time()
        item = dict(name=name, ra=ra, dec=dec,
                    position_note="Catalogue proper-motion prediction at J2026.0; no parallax or image identification.")
        try:
            result = Irsa.query_sia(pos=(SkyCoord(ra, dec, unit="deg"), 2*u.arcmin), collection=["spherex_dr1"])
            table = result.to_table() if hasattr(result, "to_table") else result
            slug = name.lower().replace(" ", "_").replace("'", "")
            table.write(output / f"{slug}.ecsv", overwrite=True)
            item.update(count=len(table), columns=table.colnames)
            if len(table):
                item.update(mjd_min=float(min(table["t_min"])), mjd_max=float(max(table["t_max"])),
                            sample_url=str(table["access_url"][0]))
        except Exception as exc:
            item["error"] = f"{type(exc).__name__}: {exc}"
        item["elapsed_seconds"] = round(time.time()-started, 2)
        report.append(item)
        (output / "coverage.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(item), flush=True)

if __name__ == "__main__":
    main()
