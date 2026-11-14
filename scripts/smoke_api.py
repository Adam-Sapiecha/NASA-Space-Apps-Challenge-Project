"""Exercise the actual local server, process worker and saved real-data products."""
import json
import time
from io import BytesIO
from pathlib import Path
import httpx
from astropy.io import fits

def main():
    demo = json.loads(Path("data/demo.json").read_text(encoding="utf-8"))
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=30) as client:
        assert client.get("/api/health").json()["status"] == "ok"
        source = client.get(f"/api/analyses/{demo['id']}").json()
        candidates = []
        for i, a in enumerate(source["frames"]):
            for b in source["frames"][i+1:]:
                if min(a["coverage"], b["coverage"]) >= .8 and abs(a["wavelength_um"]-b["wavelength_um"]) <= min(a["bandwidth_um"],b["bandwidth_um"])/2:
                    candidates.append((abs(a["mjd"]-b["mjd"]), [a["id"],b["id"]]))
        assert candidates, "No spectrally comparable temporal pair in the actual demonstration."
        baseline, ids = max(candidates,key=lambda c:c[0])
        response = client.post("/api/analyses", json=dict(search_id=demo["search_id"], observation_ids=ids))
        response.raise_for_status()
        id = response.json()["id"]
        for _ in range(60):
            job = client.get(f"/api/jobs/{id}").json()
            if job["status"] in ("complete", "failed"):
                break
            time.sleep(1)
        assert job["status"] == "complete", job
        analysis = client.get(f"/api/analyses/{id}").json()
        assert len(analysis["frames"]) == 2
        for frame in analysis["frames"]:
            image = client.get(frame["image"])
            assert image.status_code == 200 and image.content.startswith(b"\x89PNG")
            product = client.get(frame["image"].replace(".png",".fits"))
            product.raise_for_status()
            with fits.open(BytesIO(product.content)) as hdus:
                assert hdus[0].header["BUNIT"] == frame["unit"]
        sample = client.get(f"/api/analyses/{id}/sample?x=.5&y=.5")
        sample.raise_for_status()
        assert len(sample.json()["frames"]) == 2
        export = client.get(f"/api/analyses/{id}/export")
        assert export.status_code == 200 and export.json()["id"] == id
        assert client.get("/").status_code == 200
        result = dict(status="passed", id=id, baseline_days=baseline, checks=["health","process worker","two real FITS","PNG","FITS units","spectral sample","manifest export","frontend"])
        Path("data/smoke_api.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
        print(json.dumps(result))

if __name__ == "__main__":
    main()
