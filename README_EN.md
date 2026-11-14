# SPHEREx image comparison prototype

This team concept connects real NASA infrared images, wavelength exploration and inspection of apparent changes over time. No project name has been assigned. The opening example demonstrates visible motion of the known comet 3I/ATLAS. The five required targets have no confirmed motion or variability; no new discovery is claimed.

## Open the result

- English interface with a Polish language option: `http://127.0.0.1:8000/`.
- English real-data replay: `http://127.0.0.1:8000/demo/`.
- Offline replay: open `frontend/public/demo/index.html` directly in a browser. It embeds actual SPHEREx previews and their provenance. `evidence.html` beside it is a saved English evidence card.
- A saved live note: `/?analysis=4812094a2ce843a8b787837eb13ec845&note=a6971713a10c44bf8ca7045c5c748759`.

The replay does not query new coordinates. The full backend must be deployed to provide public searches. **No public service has been deployed.** See [deployment instructions](DEPLOYMENT.md).

## Run on Windows

```powershell
uv sync --python 3.12
npm.cmd ci --prefix frontend
npm.cmd run build --prefix frontend
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

Use one application process and keep `data/` for saved analyses, native FITS, images and SQLite records. Archive searches and uncached external products require a network connection. A frontend build alone does not reload the Python process. `/api/health` reports whether files have changed since the backend loaded.

## Workflow

The first visit opens real comet motion in the simple interface. Advanced tools remain available. Automatic time-series preparation checks a bounded sample across detectors for local bands, flags, aperture coverage and background before choosing dates. Its report is retained with the analysis.

Enter RA/Dec in degrees or RA hourangle and signed Dec. Prepare available SPHEREx observations, inspect dates with a common WCS/brightness stretch, or open the separate wavelength player. Select a point to inspect local wavelengths, flags and exploratory photometry. Save a human assessment and export English HTML or JSON with observation provenance. Two route anchors are a hypothesis, not an orbit.

Catalogue presets are proper-motion predictions around J2026.0; original reference epochs and sources are retained in `backend/targets.json`. They are not source detections. A sparse multi-date set of wavelength measurements is not a simultaneous spectrum. Similar centre wavelengths do not establish equal spectral response. Native aperture/ePSF errors are random only, with additional calibration, PSF, neighbour and motion uncertainties. HiPS is a multi-date context mosaic; MOST searches known objects.

## Evidence and submission materials

- [English submission draft, references, SI/AI disclosure and demo script](PAKIET_ZGLOSZENIA_EN.md).
- [Latest selection changes and five-field results](WDROZENIE_EN_I_DOBORU_OBSERWACJI.md). Epsilon Indi B now has a valid D4 pair; WISE 0855 has a D6 pair separated by about 370 days. The other three fields remain inconclusive for aperture photometry.
- [Five-field test report](WYNIKI_5_OBIEKTOW.md) and [repair audit](AUDYT_NAPRAWY.md), in Polish.
- Optional independent Photutils 3.1.1 validation is isolated under `.cache/validation-libs`; it is not a production dependency.
- Asset/library credits and licences: [ASSET_SOURCES.md](ASSET_SOURCES.md), lockfiles and `frontend/public/licenses/`.

The original concept belongs to the team. Codex assisted implementation, debugging, validation scripts and text. The team must review the final submission and accurately identify every external contribution. No AI-generated astronomy imagery is used.

The application makes essential use of [NASA SPHEREx data served by IRSA](https://irsa.ipac.caltech.edu/Missions/spherex.html). Full acknowledgement is included in the English demo and submission draft.
