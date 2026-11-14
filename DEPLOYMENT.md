# Deployment and real-data fallback

Prepared on 14 November 2026. **No public service has been deployed.** The team confirmed that it has no hosting account or public demo. The configuration below has not been executed in Docker on this computer; Docker is unavailable here. A static host can serve the English replay, but it cannot run this Python/Astropy backend.

The user explicitly selected a **local-only package** instead of public demo publication. A private Sites project was registered during preparation, but it has no deployed version. Its isolated staging copy is `submission-demo-site-20261114/`; do not push or publish it without a new instruction. The canonical demo remains in `frontend/public/demo/`.

## Deliverables

- `Dockerfile`: existing FastAPI + React application, including the shared catalogue presets.
- `compose.public.yaml` and `deploy/Caddyfile`: one application process, persistent observations volume, health check, HTTPS reverse proxy and a 4 MB request-body limit.
- `.cache/demo-seed.zip`: six prepared analyses, their original cached FITS, aligned products, scripted audit measurements and the explicitly selected demo note. The original user workspace database is **not** copied. File hashes and package size: `data/audit/demo-seed.json`.
- `frontend/public/demo/index.html`: self-contained English replay with real embedded images, dates, source URLs and native FITS SHA-256 values. Open directly for an offline demonstration.
- `frontend/public/demo/evidence.html`: English saved evidence card with embedded images and selected-point marker.

## Bring up a public backend

Use an existing Linux Docker machine with an assigned public hostname. The team must supply the host/account and DNS; this document does not authorize a purchase or create an account. Allow inbound HTTP/HTTPS. The initial allocation of two CPUs and 3 GB memory is a starting limit, not a benchmarked capacity guarantee. Keep one Uvicorn application process because the queue is local to that process.

On the host, in the uploaded project directory:

```sh
export SPHEREX_DOMAIN=your-actual-hostname
docker compose -f compose.public.yaml build
docker compose -f compose.public.yaml up -d
docker compose -f compose.public.yaml ps
```

Replace the hostname before running. Caddy uses it for HTTPS; DNS must resolve to the machine. No cloud provider, paid plan or domain has been selected.

## Seed a new, empty data volume

Copy `.cache/demo-seed.zip` onto the host. Stop only this application's service while importing; do not overwrite an existing populated workspace. The import refuses an existing database and refuses ZIP paths escaping `/app/data`.

```sh
docker compose -f compose.public.yaml stop app
docker compose -f compose.public.yaml run --rm --no-deps -v "$PWD/demo-seed.zip:/tmp/demo-seed.zip:ro" app python -c 'from pathlib import Path; from zipfile import ZipFile; root=Path("/app/data").resolve(); assert not (root/"workspace.sqlite").exists(), "Existing database: use a fresh volume or back it up first"; z=ZipFile("/tmp/demo-seed.zip"); assert all((root/n).resolve().is_relative_to(root) for n in z.namelist()); z.extractall(root)'
docker compose -f compose.public.yaml up -d app
```

Keep the ZIP's filename consistent with its upload location. Do not use `docker compose down -v`; that removes the persistent volume. Back up the volume and SQLite consistently before replacing or migrating it.

## Acceptance at the real public address

```sh
python scripts/smoke_submission.py https://your-actual-hostname --output data/audit/public-submission-smoke.json
```

Then open the link on a second device without the development computer's cookies. Test a fresh RA/Dec query, prepare at least two observations, play/pause, save a note, reopen it after a server restart and verify HTTPS. This last manual/public check remains outstanding.

Prepared example: `/?analysis=4812094a2ce843a8b787837eb13ec845&note=a6971713a10c44bf8ca7045c5c748759`.

## Operational limits

The prototype has a three-job admission limit, a single worker, bounded requests and persistent cache. It has no accounts, durable queue, request rate limiting or automated disk eviction. Restrict operational use to the hackathon demonstration until these limits are reviewed. Notes are accessible to anyone holding their links; do not enter personal information. Cache growth and external IRSA outages remain possible. The seed supports prepared analyses and native aperture measurements offline; new archive queries, uncached calibrations, HiPS tiles and external catalogues still require the network.

If `/api/health` reports `code_changed: true`, the running backend differs from files on disk: restart this service after active work finishes. A frontend build alone does not reload Python. If a worker dies, jobs now report failure rather than remaining in progress. Restart the single server and retry; successful saved analyses remain available.

## Sources

- [Docker Compose health and startup order](https://docs.docker.com/compose/how-tos/startup-order/).
- [Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy) and [request body limits](https://caddyserver.com/docs/caddyfile/directives/request_body).
- [SPHEREx at IRSA](https://irsa.ipac.caltech.edu/Missions/spherex.html).
