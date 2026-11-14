"""Prepare a real-data example, retaining provenance. Run from repository root."""
import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.archive import search
from backend.science import build_analysis
from backend.store import get, put, ROOT
from backend.targets import TARGETS

def main():
    target = next(t for t in TARGETS if t['id']=='barnard')
    source = search(str(target['field_ra']), str(target['field_dec']), 12, "spherex_dr1")
    source["id"] = uuid.uuid4().hex
    put("search", source["id"], source)
    rows = [o for o in source["observations"] if o["band"] == "SPHEREx-D2"]
    if len(rows)<2:
        raise RuntimeError("Not enough actual D2 observations.")
    ids = [rows[round(i*(len(rows)-1)/11)]["id"] for i in range(min(12,len(rows)))] if len(rows)>=12 else [o["id"] for o in rows]
    id = uuid.uuid4().hex
    print(f"Building real analysis {id}, {len(ids)} frames", flush=True)
    build_analysis(id, source, ids)
    status = get("job", id)
    print(json.dumps(status), flush=True)
    result = get("analysis", id)
    if result:
        summary = dict(id=id, search_id=source["id"],frames=[dict(id=f["id"], date=f["date"],wavelength_um=f["wavelength_um"],bandwidth_um=f["bandwidth_um"],coverage=f["coverage"]) for f in result["frames"]],failures=result["failures"])
        (ROOT / "demo.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary), flush=True)
    else:
        raise RuntimeError(status["message"])

if __name__ == "__main__":
    main()
