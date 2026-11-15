# SPHEREx Sky Explorer

Explore a fixed sky field over time and across infrared detector ranges using real SPHEREx observations. An independent NASA Space Apps Challenge prototype built with React, TypeScript and FastAPI.

- [Open the application on GitHub Pages](https://adam-sapiecha.github.io/NASA-Space-Apps-Challenge-Project/)
- [Open the full application on the server](https://luxonis.tail6ad453.ts.net:8443/spherex/)

GitHub Pages serves the frontend. Image preparation, archive searches and measurements run on the Python server.

## Use the application

1. Open a prepared example: WISE 0855, the field around Barnard’s Star, or comet 3I/ATLAS. Alternatively, choose your own field using an object list, a sky map, or coordinates.
2. Move through actual observation times, including multiple exposures on one UTC day. The default timeline uses prepared images for fast browsing. Enable **Include images that need downloading** to access the remaining archive observations.
3. Change the detector range available on that day. The app prefers a prepared exposure and explicitly shows a changed observation time. The actual local wavelength remains visible with the image.
4. Pin an image as A to compare it with later observations. Shared or separate brightness settings, optional wavelength colour and quality overlays are available.
5. Copy a link to preserve the selected analysis and display settings.

English and Polish interfaces are included. The offline English replay in `frontend/public/demo/index.html` contains embedded real images and provenance.

## Scientific limits

- Missing coverage stays missing. Solid background marks unavailable pixels; hatching is optional. The displayed coverage percentage refers to the current preview.
- The same detector does not guarantee the same local wavelength. Different times, spectral responses, backgrounds and PSFs can change an image’s appearance.
- Visual comparison and exploratory measurements do not establish a discovery, a precise motion measurement, or scientifically validated variability.
- The sky map is a mosaic of many dates. Changing its wavelength does not change its time.
- Prepared observations remain usable during IRSA outages. New, uncached fields and external catalogue/calibration requests require archive access.

## Run locally

Requires Python 3.12, Node.js 22 and [uv](https://docs.astral.sh/uv/).

```powershell
uv sync --python 3.12
cd frontend
npm ci
npm run build
cd ..
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`. A fresh checkout has an empty observation cache: search and prepare your own field, or open the standalone offline replay. The deployed server contains a curated demonstration seed. Local `data/`, caches, credentials and project notes are excluded from Git.

For frontend development, run `npm run dev` in `frontend`; Vite proxies `/api` to the local Python server. `start.ps1` builds and starts the local application.

## Deploy on a server

`Dockerfile` builds the frontend and Python service. `compose.server.yaml` provides a persistent data directory, localhost-only port binding, health check and resource limits. It supports a reverse proxy mounted at a prefix such as `/spherex`.

Set these variables in a local deployment environment file:

```text
SPHEREX_RELEASE=<source-commit>
SPHEREX_PORT=8093
SPHEREX_URL_PREFIX=/spherex
SPHEREX_PUBLIC_BASE_URL=https://your-server.example/spherex
SPHEREX_CORS_ORIGINS=https://your-account.github.io
SPHEREX_DATA_PATH=/absolute/path/to/persistent/data
```

Then build and start only this Compose project:

```sh
docker compose --env-file server.env -f compose.server.yaml build
docker compose --env-file server.env -f compose.server.yaml up -d
```

Point the reverse proxy at the bound localhost port. Keep one application process: the queue and its worker are local to that process. Back up the persistent SQLite database and observation files before upgrades. This demonstration service has bounded jobs but no accounts, durable distributed queue or automated cache eviction.

`scripts/package_demo.py` can package a curated seed from an existing audited workspace. It excludes the full user database, credentials and unselected notes. Do not import a seed over a populated workspace.

## GitHub Pages

The Pages workflow builds the same frontend using the repository name as its asset prefix. Configure the public repository variable **SPHEREX_API_URL** to the backend’s public base URL, for example `https://your-server.example/spherex`. Set the Pages publishing source to **GitHub Actions**. The backend must allow the exact Pages origin through `SPHEREX_CORS_ORIGINS`.

The workflow runs frontend tests, checks the backend’s health and publishes the built static files. The Python backend cannot run on GitHub Pages.

## Verification

```powershell
cd frontend
npm test
npm run build
cd ..
.\.venv\Scripts\python.exe -m pytest -q
```

Deployment tests cover prefixed API/static routes, application lifecycle and CORS. Frontend tests cover temporal and spectral navigation, stable ordering, cached browsing, deployment URLs and coordinate mapping.

The `scripts/` directory contains tools for preparing and exporting real-data demos, packaging a curated server seed, checking the live API and validating the five target fields. These tools require the local observations and audit inputs described in their source; automated tests run independently of those saved reports. Generated reports, local notes and caches stay outside Git and the Docker build context.

## Data and attribution

- [SPHEREx at NASA/IPAC IRSA](https://irsa.ipac.caltech.edu/Missions/spherex.html)
- [IRSA SPHEREx tutorials and FITS documentation](https://caltech-ipac.github.io/irsa-tutorials/)
- [NASA/IPAC observations of 3I/ATLAS](https://irsa.ipac.caltech.edu/data/SPHEREx/docs/comet3iatlas/)
- Sky context: Aladin Lite, IRSA SPHEREx HiPS, 2MASS and AllWISE; optional catalogue context includes Gaia and SIMBAD.

Bundled third-party asset notices are in `frontend/public/licenses/`. Observation manifests retain archive URLs and native FITS checksums. This independent project does not imply NASA endorsement.
