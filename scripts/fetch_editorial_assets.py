import hashlib
import json
from io import BytesIO
from pathlib import Path

import httpx
from PIL import Image, ImageChops

PAGE = "https://www.jpl.nasa.gov/news/how-nasas-spherex-mission-will-share-its-all-sky-map-with-the-world/"
POLICY = "https://www.jpl.nasa.gov/jpl-image-use-policy/"
ASSETS = [
    ("spherex-vela.png", "https://d2pn8kiwq2w21t.cloudfront.net/images/1-PIA26354-SPHEREx-data.width-1320.png", "SPHEREx observation of the Vela Molecular Ridge, including RCW 36."),
    ("spherex-329um.png", "https://d2pn8kiwq2w21t.cloudfront.net/images/e2a_spherex.width-1024.png", "SPHEREx early test observation, April 2025, at 3.29 micrometres."),
    ("spherex-098um.png", "https://d2pn8kiwq2w21t.cloudfront.net/images/e2b_spherex.width-1024.png", "Same field observed by SPHEREx at 0.98 micrometres; a wavelength comparison, not a time comparison."),
]

def main():
    directory = Path("frontend/public/images")
    directory.mkdir(parents=True, exist_ok=True)
    originals = Path("data/editorial-originals")
    originals.mkdir(parents=True, exist_ok=True)
    manifest = []
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        for filename, url, description in ASSETS:
            original_path = originals / filename
            if original_path.exists():
                content = original_path.read_bytes()
            elif (directory / filename).exists():
                content = (directory / filename).read_bytes()
            else:
                response = client.get(url)
                response.raise_for_status()
                content = response.content
            original_path.write_bytes(content)
            image = Image.open(BytesIO(content)).convert("RGBA")
            output_name = Path(filename).with_suffix(".webp").name
            output_path = directory / output_name
            image.save(output_path, format="WEBP", lossless=True, method=6)
            with Image.open(output_path) as decoded:
                difference = ImageChops.difference(image, decoded.convert("RGBA"))
                assert all(high == 0 for low, high in difference.getextrema())
            (directory / filename).unlink(missing_ok=True)
            manifest.append(dict(filename=output_name, source_page=PAGE, source_url=url,
                                 credit="NASA/JPL-Caltech", usage_policy=POLICY,
                                 usage="Editorial and educational use with credit, per JPL Image Use Policy. No endorsement implied.",
                                 description=description, width=image.width, height=image.height,
                                 original_sha256=hashlib.sha256(content).hexdigest(),
                                 asset_sha256=hashlib.sha256(output_path.read_bytes()).hexdigest(),
                                 modifications="Lossless WebP encoding; decoded RGBA pixels verified identical. CSS may crop the introductory figure."))
            print(f"{output_name}: {image.width} x {image.height}, {output_path.stat().st_size} bytes, lossless verified", flush=True)
    (directory / "sources.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
