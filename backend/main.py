import re
import os
import uuid
import hashlib
import logging
from typing import Literal
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend import archive, store
from backend.science import build_analysis
from backend.orientation import direction, footprint
from backend.science import output_wcs, PIPELINE_VERSION
from backend.measurements import measure, recommend
from backend.change_diagnostics import diagnose
from backend.temporal import product
from backend.catalogs import gaia
from backend.previews import make_previews
from backend.irsa_jobs import run_job as run_irsa_job
from backend.irsa_resources import hips_metadata, layer_properties, hips_tile, hips_allsky
from backend.reference_spectra import compare_reference
from backend.targets import target_fields
from backend.evidence import evidence, evidence_html
from backend.source_assessment import source_record, identify, quality_report, weighted_flux

pool = None

def source_fingerprint():
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob('*.py')):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    digest.update(Path(__file__).with_name('targets.json').read_bytes())
    return digest.hexdigest()

LOADED_SOURCE = source_fingerprint()
STARTED_AT = datetime.now(timezone.utc).isoformat()

def submit_job(id, function, *args):
    """Surface worker death instead of leaving a job in 'running' forever."""
    try:
        if pool is None:
            raise RuntimeError('worker not started')
        future = pool.submit(function, id, *args)
    except Exception as exc:
        store.put('job', id, dict(id=id, status='failed', message='Proces obliczeniowy niedostępny. Uruchom serwer ponownie.'))
        raise HTTPException(503, 'Proces obliczeniowy niedostępny. Uruchom serwer ponownie.') from exc
    def completed(result):
        try:
            result.result()
        except BaseException:
            store.put('job', id, dict(id=id, status='failed', message='Proces obliczeniowy został przerwany. Ponów po restarcie serwera.'))
    future.add_done_callback(completed)

@asynccontextmanager
async def lifespan(app):
    global pool
    # Interrupted jobs are explicit on restart; there is no durable queue yet.
    with store.connect() as db:
        rows = db.execute("SELECT id, body FROM records WHERE kind='job'").fetchall()
    import json
    for id, body in rows:
        if json.loads(body)["status"] in ("queued", "running"):
            store.put("job", id, dict(id=id, status="failed", message="Proces został przerwany. Uruchom analizę ponownie."))
    pool = ProcessPoolExecutor(max_workers=1)
    yield
    pool.shutdown(wait=False, cancel_futures=True)

app = FastAPI(title="SPHEREx image comparison", lifespan=lifespan)

class SearchRequest(BaseModel):
    ra: str = Field(max_length=60)
    dec: str = Field(max_length=60)
    fov_arcmin: float = Field(default=12, ge=2, le=30, allow_inf_nan=False)
    collection: str = "spherex_dr1"

class AnalysisRequest(BaseModel):
    search_id: str
    observation_ids: list[str] = Field(min_length=1, max_length=12)
    retry_of: str | None = Field(default=None, max_length=100)


class AutoAnalysisRequest(BaseModel):
    search_id: str = Field(max_length=100)
    target_id: str | None = Field(default=None, max_length=50)
    candidate_limit: int = Field(default=36, ge=12, le=48)
    radius_arcsec: float = Field(default=12.4, ge=6.2, le=30, allow_inf_nan=False)


@app.post('/api/analyses/auto', status_code=202)
def automatic_analysis(request: AutoAnalysisRequest):
    from backend.observation_selection import resolve_target, build_selected_analysis
    source = record('search', request.search_id)
    try:
        resolve_target(source, request.target_id)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    with store.connect() as db:
        import json
        active = sum(json.loads(row[0])['status'] in ('queued', 'running')
                     for row in db.execute("SELECT body FROM records WHERE kind='job'"))
    if active >= 3:
        raise HTTPException(429, 'The processing queue is full. Wait for a running job to finish.')
    id = uuid.uuid4().hex
    store.put('job', id, dict(id=id, status='queued', completed=0, total=request.candidate_limit,
                             phase='selection', message='Waiting to check local bands, masks and observation dates.'))
    submit_job(id, build_selected_analysis, source, request.target_id, request.candidate_limit, request.radius_arcsec)
    return dict(id=id)


@app.get('/api/selections/{id}')
def selection_report(id: str):
    return record('selection', id)

class NotePoint(BaseModel):
    x: float = Field(ge=0, le=1, allow_inf_nan=False)
    y: float = Field(ge=0, le=1, allow_inf_nan=False)

class NoteAnchor(NotePoint):
    frameId: str = Field(max_length=100)
    mjd: float = Field(allow_inf_nan=False)

class NoteRequest(BaseModel):
    kind: Literal['motion', 'brightness', 'uncertain'] = 'uncertain'
    text: str = Field(default='', max_length=3000)
    frame_ids: list[str] = Field(min_length=2, max_length=2)
    point: NotePoint | None = None
    anchors: list[NoteAnchor] = Field(default_factory=list, max_length=2)
    route_checks: dict[str, Literal['fits', 'misses', 'unknown']] = Field(default_factory=dict, max_length=12)
    mode: Literal['side', 'lens', 'blink', 'route', 'series'] = 'side'
    quality: Literal['all', 'valid'] = 'all'
    range_mode: Literal['standard', 'faint', 'full'] = 'standard'
    series_only: bool = True
    measurement_id: str | None = Field(default=None, max_length=100)

@app.post('/api/analyses/{id}/notes', status_code=201)
def save_note(id: str, request: NoteRequest):
    manifest = record('analysis', id)
    frames = {f['id']: f for f in manifest['frames']}
    if not set(request.frame_ids) <= frames.keys() or not request.route_checks.keys() <= frames.keys():
        raise HTTPException(422, 'Karta musi dotyczyć klatek tej analizy.')
    if len(request.anchors) not in (0, 2) or any(a.frameId not in frames or a.mjd != frames[a.frameId]['mjd'] for a in request.anchors):
        raise HTTPException(422, 'Trasa musi zawierać dwie pozycje z datami klatek tej analizy.')
    if request.anchors and request.anchors[0].mjd == request.anchors[1].mjd:
        raise HTTPException(422, 'Trasa wymaga dwóch różnych terminów.')
    anchor_ids = {a.frameId for a in request.anchors}
    if request.route_checks and (not request.anchors or set(request.route_checks) & anchor_ids):
        raise HTTPException(422, 'Sprawdź trasę w obserwacji innej niż jej dwa punkty odniesienia.')
    if any(frames[f]['mjd'] in {a.mjd for a in request.anchors} for f in request.route_checks):
        raise HTTPException(422, 'Sprawdzenie trasy wymaga kolejnego terminu obserwacji.')
    if request.measurement_id:
        measured = record('measurement', request.measurement_id)
        if measured['analysis_id'] != id or not request.point or measured.get('point') != request.point.model_dump():
            raise HTTPException(422, 'Zapisany pomiar musi dotyczyć punktu tej karty i tej samej analizy.')
    note_id = uuid.uuid4().hex
    note = dict(id=note_id, analysis_id=id, created_at=datetime.now(timezone.utc).isoformat(),
                **request.model_dump(), limitations=['Notatka i ocena trasy pochodzą od użytkownika. Nie potwierdzają ruchu ani zmienności.'])
    store.put('note', note_id, note)
    return note

@app.get('/api/notes/{id}')
def read_note(id: str):
    return record('note', id)

@app.get('/api/notes/{id}/evidence')
def note_evidence(id: str):
    note = record('note', id)
    measured = record('measurement', note['measurement_id']) if note.get('measurement_id') else None
    return evidence(note, record('analysis', note['analysis_id']), measured)

@app.get('/api/notes/{id}/evidence.html')
def portable_evidence(id: str):
    return Response(evidence_html(note_evidence(id)), media_type='text/html',
                    headers={'Content-Disposition': f'attachment; filename="spherex-evidence-{id}.html"',
                             'Content-Security-Policy': "default-src 'none'; img-src data:; style-src 'unsafe-inline'; base-uri 'none'"})

class OrientationRequest(BaseModel):
    ra: float = Field(ge=0, lt=360, allow_inf_nan=False)
    dec: float = Field(ge=-90, le=90, allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    height_m: float = Field(default=0, ge=-500, le=10000, allow_inf_nan=False)
    utc: str | None = Field(default=None, max_length=40)

class MeasurementRequest(BaseModel):
    x: float = Field(ge=0, le=1, allow_inf_nan=False)
    y: float = Field(ge=0, le=1, allow_inf_nan=False)
    radius_arcsec: float = Field(default=12.4, ge=6.2, le=30, allow_inf_nan=False)

class DiscoveryRequest(BaseModel):
    frame_id: str = Field(max_length=100)
    threshold: float = Field(default=5,ge=3,le=15,allow_inf_nan=False)
    minarea: int = Field(default=3,ge=3,le=20)

class IdentificationRequest(NotePoint):
    frame_id: str = Field(max_length=100)
    radius_arcsec: float = Field(default=12.4, ge=1, le=60, allow_inf_nan=False)

class QualityLabelRequest(BaseModel):
    frame_id: str = Field(max_length=100)
    label: Literal['source', 'artifact', 'blend', 'uncertain']
    reason: str = Field(min_length=3, max_length=2000, pattern=r'\S')

class WeightedFluxRequest(BaseModel):
    frame_ids: list[str] = Field(min_length=2, max_length=12)
    max_hours: float = Field(default=24, gt=0, le=48, allow_inf_nan=False)

@app.post('/api/analyses/{id}/sources')
def create_source(id: str, request: NotePoint):
    return source_record(record('analysis', id), **request.model_dump())

@app.get('/api/sources/{id}')
def read_source(id: str):
    return record('source', id)

@app.post('/api/analyses/{id}/identification')
def identify_source(id: str, request: IdentificationRequest):
    manifest = record('analysis', id)
    if request.frame_id not in {f['id'] for f in manifest['frames']}:
        raise HTTPException(422, 'Wybierz ekspozycję tej analizy.')
    try:
        return identify(manifest, **request.model_dump())
    except Exception as exc:
        raise HTTPException(502, 'Katalog Gaia niedostępny. Zapisane analizy pozostają dostępne.') from exc

@app.post('/api/analyses/{id}/quality')
def source_quality(id: str, request: MeasurementRequest):
    try:
        return quality_report(record('analysis', id), **request.model_dump())
    except (ValueError, KeyError, OSError) as exc:
        raise HTTPException(422, str(exc)) from exc

@app.get('/api/quality/{id}')
def read_quality(id: str):
    return record('quality_report', id)

@app.get('/api/identifications/{id}')
def read_identification(id: str):
    return record('identification', id)

@app.get('/api/quality/{id}/labels')
def read_quality_labels(id: str):
    record('quality_report', id)
    import json
    with store.connect() as db:
        rows = db.execute("SELECT body FROM records WHERE kind='quality_label'").fetchall()
    return [value for row in rows if (value := json.loads(row[0]))['quality_report_id'] == id]

@app.post('/api/quality/{id}/labels', status_code=201)
def label_quality(id: str, request: QualityLabelRequest):
    report = record('quality_report', id)
    if request.frame_id not in {r['frame_id'] for r in report['rows']}:
        raise HTTPException(422, 'Ekspozycja nie należy do raportu jakości.')
    if not request.reason.strip():
        raise HTTPException(422, 'Podaj uzasadnienie oceny.')
    key = uuid.uuid4().hex
    label = dict(id=key, quality_report_id=id, source_id=report['source_id'],
                 analysis_id=report['analysis_id'], measurement_id=report['measurement_id'],
                 created_at=datetime.now(timezone.utc).isoformat(),
                 provenance='unverified_user_assessment', **request.model_dump())
    store.put('quality_label', key, label)
    return label

@app.post('/api/irsa/results/{id}/weighted-flux')
def combine_flux(id: str, request: WeightedFluxRequest):
    report = record('irsa_result', id)
    if report.get('kind') != 'calibrated':
        raise HTTPException(422, 'Wybierz raport pomiarów kalibrowanych ePSF.')
    try:
        result = weighted_flux(report, **request.model_dump())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    result.update(calibrated_result_id=id, analysis_id=report['analysis_id'])
    key = hashlib.sha256((id+str(request.model_dump())+result['method']).encode()).hexdigest()
    result['id'] = key
    store.put('weighted_flux', key, result)
    return result

@app.get('/api/weighted-flux/{id}')
def read_weighted_flux(id: str):
    return record('weighted_flux', id)

class MostRequest(BaseModel):
    name: str = Field(min_length=1,max_length=100,pattern=r'^[\w .():/+\-]+$')
    start_date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')

class ReferenceRequest(BaseModel):
    calibrated_id: str = Field(max_length=100)
    format: Literal['votable','csv']
    content: str = Field(max_length=3*1024*1024)

def enqueue_irsa(kind,manifest,settings):
    import json
    with store.connect() as db:
        active=sum(json.loads(row[0])['status'] in ('queued','running') for row in db.execute("SELECT body FROM records WHERE kind='job'"))
    if active>=3: raise HTTPException(429,'Kolejka jest pełna. Poczekaj na zakończenie obliczeń.')
    id=uuid.uuid4().hex
    store.put('job',id,dict(id=id,status='queued',completed=0,total=1,message='Oczekiwanie na zadanie IRSA'))
    submit_job(id,run_irsa_job,kind,manifest,settings)
    return dict(id=id)

@app.get('/api/irsa/hips')
def irsa_hips():
    try:return hips_metadata()
    except Exception as exc:raise HTTPException(502,'Metadane mapy SPHEREx są niedostępne.') from exc

@app.get('/api/irsa/hips/layers/{index}/properties')
def irsa_layer_properties(index:int,request:Request):
    try:return Response(layer_properties(index,os.environ.get('SPHEREX_PUBLIC_BASE_URL') or str(request.base_url).rstrip('/')),media_type='text/plain')
    except ValueError as exc:raise HTTPException(404,str(exc)) from exc
    except Exception as exc:raise HTTPException(502,'Metadane mapy SPHEREx są niedostępne.') from exc

@app.get('/api/irsa/hips/layers/{index}/Norder{order}/Dir{directory}/Npix{pixel}.png')
def irsa_layer_tile(index:int,order:int,directory:int,pixel:int):
    try:return Response(hips_tile(index,order,directory,pixel),media_type='image/png',headers={'Cache-Control':'public, max-age=86400'})
    except ValueError as exc:raise HTTPException(404,str(exc)) from exc
    except Exception as exc:raise HTTPException(502,'Kafelek SPHEREx niedostępny.') from exc

@app.get('/api/irsa/hips/layers/{index}/Norder3/Allsky.png')
def irsa_layer_allsky(index:int):
    try:return Response(hips_allsky(index),media_type='image/png',headers={'Cache-Control':'public, max-age=86400'})
    except ValueError as exc:raise HTTPException(404,str(exc)) from exc
    except Exception as exc:raise HTTPException(502,'Podgląd SPHEREx niedostępny.') from exc

@app.post('/api/analyses/{id}/calibrated',status_code=202)
def calibrated(id:str,request:MeasurementRequest):
    return enqueue_irsa('calibrated',record('analysis',id),request.model_dump())

@app.post('/api/analyses/{id}/discovery',status_code=202)
def discovery(id:str,request:DiscoveryRequest):
    manifest=record('analysis',id)
    if request.frame_id not in {f['id'] for f in manifest['frames']}:raise HTTPException(422,'Wybierz zdjęcie tej analizy.')
    return enqueue_irsa('discovery',manifest,request.model_dump())

@app.post('/api/irsa/most',status_code=202)
def moving_objects(request:MostRequest):
    from datetime import date
    try:
        start,end=date.fromisoformat(request.start_date),date.fromisoformat(request.end_date)
        if end<start or (end-start).days>31:raise ValueError()
    except ValueError as exc:raise HTTPException(422,'Zakres MOST musi obejmować od 0 do 31 dni.') from exc
    return enqueue_irsa('most',None,request.model_dump())

@app.get('/api/irsa/results/{id}')
def irsa_result(id:str):return record('irsa_result',id)

@app.get('/api/irsa/results/{id}/target.tbl')
def irsa_target(id:str):
    result=record('irsa_result',id)
    if result['kind']!='calibrated':raise HTTPException(404)
    return FileResponse(store.ROOT/'irsa'/id/'target.tbl',filename='spherex-target.tbl')

@app.post('/api/analyses/{id}/reference')
def reference_spectrum(id:str,request:ReferenceRequest):
    local=record('irsa_result',request.calibrated_id)
    if local['kind']!='calibrated' or local['analysis_id']!=id:raise HTTPException(422,'Wybierz kalibrację tej analizy.')
    try:return compare_reference(local,record('analysis',id),request.content,request.format)
    except (ValueError,TypeError,KeyError) as exc:raise HTTPException(422,str(exc)) from exc

class PreviewRequest(BaseModel):
    quality: str = Field(default='all', pattern='^(all|valid)$')
    range_mode: str = Field(default='standard', pattern='^(standard|faint|full)$')
    frame_ids: list[str] | None = Field(default=None, min_length=1, max_length=48)

@app.post('/api/analyses/{id}/previews')
def preview(id: str, request: PreviewRequest):
    try:
        return make_previews(record('analysis', id), **request.model_dump())
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@app.get('/api/previews/{id}/{filename}')
def preview_file(id: str, filename: str):
    source = record('preview', id)
    allowed = {f"{f['id']}{suffix}.png" for f in source['frames'] for suffix in ('', '-quality')}
    if filename not in allowed:
        raise HTTPException(404)
    return FileResponse(store.ROOT/'previews'/id/filename)

class ProductRequest(BaseModel):
    frame_ids: list[str] = Field(min_length=2, max_length=12)
    weights: list[float] = Field(min_length=2, max_length=12)
    operation: str = Field(pattern='^(stack|difference)$')
    max_hours: float = Field(default=24, ge=.01, le=48, allow_inf_nan=False)

class CatalogRequest(BaseModel):
    ra: float = Field(ge=0, lt=360, allow_inf_nan=False)
    dec: float = Field(ge=-90, le=90, allow_inf_nan=False)
    radius_arcmin: float = Field(default=10, ge=1, le=30, allow_inf_nan=False)
    mjd: float = Field(ge=15020, le=88434, allow_inf_nan=False)

@app.post('/api/catalogs/gaia')
def gaia_context(request: CatalogRequest):
    try:
        return gaia(**request.model_dump())
    except Exception as exc:
        raise HTTPException(502, 'Katalog Gaia niedostępny. Analiza SPHEREx nadal działa.') from exc

@app.post('/api/orientation')
def orientation(request: OrientationRequest):
    try:
        return direction(**request.model_dump())
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, 'Niepoprawny czas UTC lub współrzędne.') from exc

@app.post('/api/field')
def field(request: SearchRequest):
    try:
        coord = archive.coordinates(request.ra, request.dec)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return dict(ra=float(coord.ra.deg), dec=float(coord.dec.deg),
                footprint=footprint(output_wcs(coord.ra.deg, coord.dec.deg, request.fov_arcmin, 120), 120))

@app.get('/api/analyses/{id}/footprint')
def analysis_footprint(id: str):
    manifest = record('analysis', id, allow_provisional=True)
    return dict(ra=manifest['search']['ra'], dec=manifest['search']['dec'],
                footprint=footprint(manifest['wcs'], manifest['pixels']))

@app.post('/api/analyses/{id}/measurements')
def measurements(id: str, request: MeasurementRequest):
    return measure(record('analysis', id), **request.model_dump())

@app.get('/api/measurements/{id}')
def measurement_export(id: str):
    return record('measurement', id)

@app.get('/api/measurements/{id}/recommendation')
def recommendation(id: str):
    return recommend(record('measurement', id))

@app.get('/api/measurements/{id}/change-diagnostics')
def change_diagnostics(id: str, a: str = Query(max_length=100), b: str = Query(max_length=100)):
    try:
        return diagnose(record('measurement', id), a, b)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@app.post('/api/analyses/{id}/products')
def create_product(id: str, request: ProductRequest):
    try:
        return product(record('analysis', id), request.frame_ids, request.weights, request.operation, request.max_hours)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@app.get('/api/products/{id}')
def read_product(id: str):
    return record('product', id)

@app.get('/api/products/{id}/{filename}')
def product_file(id: str, filename: str):
    record('product', id)
    if filename not in ('preview.png', 'image.fits', 'manifest.json'):
        raise HTTPException(404)
    return FileResponse(store.ROOT/'products'/id/filename)

def record(kind, id, *, allow_provisional=False):
    value = store.get(kind, id)
    if value is None:
        raise HTTPException(404, "Nie znaleziono zapisu.")
    if kind == 'analysis' and value.get('provisional') and not allow_provisional:
        raise HTTPException(409, 'Download in progress. Measurements become available when all candidates have been checked.')
    return value

@app.get("/api/health")
def health():
    return dict(status="ok", pipeline=PIPELINE_VERSION, release=os.environ.get("SPHEREX_RELEASE", "local"), source_sha256=LOADED_SOURCE,
                code_changed=source_fingerprint()!=LOADED_SOURCE, started_at=STARTED_AT)

@app.get('/api/targets')
def targets(mjd: float = Query(default=61041.0, ge=60000, le=63000, allow_inf_nan=False)):
    return target_fields(mjd)

@app.get('/api/examples')
def examples():
    """Only advertise prepared examples whose actual image products still exist."""
    import json
    result = []
    for filename in ('smoke_api.json', 'demo.json'):
        try:
            info = json.loads((store.ROOT/filename).read_text(encoding='utf-8'))
            manifest = store.get('analysis', info['id'])
            if manifest and len(manifest['frames']) >= 2 and all((store.ROOT/'analyses'/manifest['id']/f"{f['id']}.png").exists() for f in manifest['frames']):
                result.append(dict(id=manifest['id'], label=info.get('label', 'Pole Barnard’s Star'), frames=len(manifest['frames'])))
        except (OSError, ValueError, KeyError):
            continue
    return result[:1]

@app.post("/api/search")
def search(request: SearchRequest):
    if request.collection not in archive.COLLECTIONS:
        raise HTTPException(422, "Nieobsługiwana kolekcja.")
    try:
        archive.coordinates(request.ra, request.dec)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    try:
        result = archive.search(**request.model_dump())
    except Exception as exc:
        cached = cached_search(request)
        if cached:
            area = cached['fov_arcmin']
            same_size = abs(area-request.fov_arcmin)<1e-7
            extent = ('Rozmiar zapisanego pola odpowiada wybranemu.' if same_size else
                      f'Wybrano {request.fov_arcmin:g}′, ale zapisane pole ma {area:g}′. '
                      'Przygotowanie zdjęć będzie dotyczyć zapisanego obszaru.')
            return {**cached, 'cached': True,
                    'requested_field':dict(ra=request.ra,dec=request.dec,fov_arcmin=request.fov_arcmin),
                    'notice': 'Archiwum IRSA jest chwilowo niedostępne. Pokazujemy wcześniej pobraną listę zdjęć. '
                    f'{extent} Środek zapisanego pola: RA {cached["ra"]:.6f}°, Dec {cached["dec"]:.6f}°. '
                    'Lista może nie obejmować nowych obserwacji.'}
        logging.getLogger(__name__).warning('IRSA search failed without cached field: %s',exc)
        raise HTTPException(502, 'Archiwum IRSA jest chwilowo niedostępne. Nie mamy zapisanej listy obserwacji '
                            'dla tego miejsca i wydania danych. Spróbuj ponownie później lub otwórz gotowy przykład ruchu na stronie głównej.') from exc
    id = uuid.uuid4().hex
    result["id"] = id
    store.put("search", id, result)
    return result


def cached_search(request: SearchRequest):
    import json
    coord = archive.coordinates(request.ra, request.dec)
    with store.connect() as db:
        rows = db.execute("SELECT body FROM records WHERE kind='search' ORDER BY rowid DESC").fetchall()
    candidates=[]
    for index,(body,) in enumerate(rows):
        saved = json.loads(body)
        if saved.get('collection') != request.collection or not saved.get('observations'):
            continue
        try:
            centre=SkyCoord(saved['ra'],saved['dec'],unit='deg')
            # At most one arcsecond tolerates rounded coordinates (well below a
            # native SPHEREx pixel). Never reuse another target or release.
            separation=float(coord.separation(centre).arcsec)
            area=float(saved['fov_arcmin'])
            if not np.isfinite(separation) or separation>1 or not np.isfinite(area) or area<=0:
                continue
        except (KeyError,ValueError,TypeError):
            continue
        candidates.append(((abs(area-request.fov_arcmin),separation,index),saved))
    # Return the actual saved geometry and ID, never relabel a 6' field as 12'.
    return min(candidates,key=lambda row:row[0])[1] if candidates else None

@app.post("/api/analyses", status_code=202)
def create_analysis(request: AnalysisRequest):
    source = record("search", request.search_id)
    previous = record('analysis', request.retry_of) if request.retry_of else None
    if previous and (previous['search']['id'] != request.search_id or
                     set(request.observation_ids) != {f['id'] for f in previous['frames']} | {f['observation'] for f in previous['failures']}):
        raise HTTPException(422, 'Ponowienie musi dotyczyć tego samego wyszukiwania i pierwotnego zestawu.')
    available = {o["id"] for o in source["observations"]}
    if len(set(request.observation_ids)) != len(request.observation_ids) or not set(request.observation_ids) <= available:
        raise HTTPException(422, "Wybierz różne obserwacje z tego wyszukiwania.")
    with store.connect() as db:
        import json
        active = sum(json.loads(row[0])["status"] in ("queued", "running") for row in db.execute("SELECT body FROM records WHERE kind='job'"))
    if active >= 3:
        raise HTTPException(429, "Kolejka jest pełna. Poczekaj na zakończenie analizy.")
    id = uuid.uuid4().hex
    store.put("job", id, dict(id=id, status="queued", completed=0, total=len(request.observation_ids), message="Oczekiwanie na przetwarzanie"))
    submit_job(id, build_analysis, source, request.observation_ids, previous, previous.get('selection') if previous else None)
    return dict(id=id)

@app.get("/api/jobs/{id}")
def job(id: str):
    return record("job", id)

@app.get("/api/analyses/{id}")
def analysis(id: str):
    return record("analysis", id, allow_provisional=True)

@app.get("/api/analyses/{id}/export")
def export(id: str):
    record("analysis", id, allow_provisional=True)
    return FileResponse(store.ROOT / "analyses" / id / "manifest.json", filename=f"analysis-{id}.json")

@app.get("/api/analyses/{id}/frames/{filename}")
def frame(id: str, filename: str):
    manifest = record("analysis", id, allow_provisional=True)
    if not re.fullmatch(r"[a-f0-9]{20}\.(png|fits)", filename) or filename.split(".")[0] not in {f["id"] for f in manifest["frames"]}:
        raise HTTPException(404)
    return FileResponse(store.ROOT / "analyses" / id / filename)

@app.get("/api/analyses/{id}/sample")
def sample(id: str, x: float = Query(ge=0, le=1, allow_inf_nan=False), y: float = Query(ge=0, le=1, allow_inf_nan=False)):
    from backend.coordinates import point_sky, point_sample
    manifest = record("analysis", id)
    point = dict(x=x, y=y)
    sky = point_sky(manifest, point)
    frames = []
    for f in manifest["frames"]:
        with np.load(store.ROOT / "analyses" / id / f"{f['id']}.npz") as data:
            local = point_sample(manifest, point, data)
            flags = local.pop('flags_word')
            frames.append(dict(id=f['id'], **local,
                               flags=[name for name, bit in f['flag_definitions'].items() if flags & (1<<bit)]))
    return dict(ra=sky.ra.deg, dec=sky.dec.deg, point=point, coordinate_method='continuous-point-1',
                wavelength_method='bilinear-WCS-WAVE-browsing', quality_location='containing output pixel', frames=frames)

from backend.analysis_api import router as analysis_router
app.include_router(analysis_router)
from backend.comparison_api import router as comparison_router
app.include_router(comparison_router)

dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if dist.exists():
    app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
