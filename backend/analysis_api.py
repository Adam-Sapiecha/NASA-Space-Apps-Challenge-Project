"""Typed entry points for the complete source-analysis workbench."""
import hashlib
import json
from datetime import datetime, timezone
from typing import Literal

from astropy.time import Time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from backend import store

router = APIRouter()


def record(kind, key):
    value = store.get(kind, key)
    if value is None:
        raise HTTPException(404, 'Nie znaleziono zapisanego wyniku.')
    return value


def enqueue(kind, manifest, settings):
    from backend.main import enqueue_irsa
    return enqueue_irsa(kind, manifest, settings)


def save_report(result):
    key = hashlib.sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest()
    result.update(id=key, created_at=datetime.now(timezone.utc).isoformat())
    store.put('irsa_result', key, result)
    return result


class Point(BaseModel):
    model_config = ConfigDict(extra='forbid')
    x: float = Field(ge=0, le=1, allow_inf_nan=False)
    y: float = Field(ge=0, le=1, allow_inf_nan=False)


class Context(Point):
    frame_id: str = Field(min_length=1, max_length=100)
    radius_arcsec: float = Field(default=12.4, ge=1, le=60, allow_inf_nan=False)


@router.post('/api/analyses/{id}/context', status_code=202)
def context(id: str, request: Context):
    manifest = record('analysis', id)
    if request.frame_id not in {f['id'] for f in manifest['frames']}:
        raise HTTPException(422, 'Ekspozycja nie należy do analizy.')
    return enqueue('context', manifest, request.model_dump())


@router.post('/api/analyses/{id}/profile', status_code=202)
def profile(id: str, request: Point):
    return enqueue('profile', record('analysis', id), request.model_dump())


class Dates(BaseModel):
    model_config = ConfigDict(extra='forbid')
    dates: list[str] = Field(min_length=1, max_length=60)


def mjds(dates):
    try:
        values = [float(Time(date, scale='utc').mjd) for date in dates]
        if any(not 15020 <= value <= 88434 for value in values):
            raise ValueError()
        return values
    except (ValueError, TypeError):
        raise HTTPException(422, 'Podaj poprawne daty UTC z lat 1900–2100.')


class Ephemeris(Dates):
    name: str = Field(min_length=1, max_length=100, pattern=r'^[\w .()+/\-]+$')
    observer: str = Field(default='500@399', max_length=25, pattern=r'^[A-Za-z0-9\-]+@[0-9\-]+$')


@router.post('/api/ephemerides', status_code=202)
def ephemerides(request: Ephemeris):
    return enqueue('ephemeris', None, dict(name=request.name, observer=request.observer, mjds=mjds(request.dates)))


class Star(Dates):
    catalog_id: str = Field(max_length=100)
    candidate_id: str = Field(max_length=100)


@router.post('/api/star-positions')
def star_positions(request: Star):
    from backend.trajectory import star_positions as propagate
    catalog = record('catalog', request.catalog_id)
    candidate = next((r for r in catalog['sources'] if r['id'] == request.candidate_id), None)
    if candidate is None:
        raise HTTPException(422, 'Źródło nie należy do zapisanego katalogu.')
    try:
        result = propagate(candidate, mjds(request.dates))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    result['catalog_id'] = request.catalog_id
    return save_report(result)


class Position(Point):
    frame_id: str = Field(max_length=100)


class Motion(Dates):
    positions: list[Position] = Field(min_length=3, max_length=12)
    systematic_floor_arcsec: float = Field(default=2, ge=.1, le=30, allow_inf_nan=False)


@router.post('/api/analyses/{id}/motion', status_code=202)
def motion(id: str, request: Motion):
    manifest = record('analysis', id)
    lookup = {f['id']: f for f in manifest['frames']}
    ids = [p.frame_id for p in request.positions]
    if len(set(ids)) != len(ids) or not set(ids) <= lookup.keys() or len({lookup[k]['mjd'] for k in ids}) < 3:
        raise HTTPException(422, 'Wybierz trzy różne ekspozycje i terminy tej analizy.')
    return enqueue('motion', manifest, dict(positions=[p.model_dump() for p in request.positions],
                   prediction_mjds=mjds(request.dates), systematic_floor_arcsec=request.systematic_floor_arcsec))


class Template(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(min_length=1, max_length=100)
    provenance: str = Field(min_length=3, max_length=500)
    wavelength_um: list[float] = Field(min_length=4, max_length=5000)
    relative_fnu: list[float] = Field(min_length=4, max_length=5000)


class Spectrum(BaseModel):
    frame_ids: list[str] = Field(min_length=4, max_length=12)
    max_hours: float = Field(default=24, gt=0, le=48, allow_inf_nan=False)
    templates: list[Template] = Field(default_factory=list, max_length=3)


@router.post('/api/irsa/results/{id}/interpret-spectrum', status_code=202)
def spectrum(id: str, request: Spectrum):
    report = record('irsa_result', id)
    if report.get('kind') != 'calibrated':
        raise HTTPException(422, 'Wymagany raport kalibrowanej fotometrii ePSF.')
    if len(set(request.frame_ids)) != len(request.frame_ids) or not set(request.frame_ids) <= {r['id'] for r in report['rows']}:
        raise HTTPException(422, 'Wybierz różne pomiary tego raportu.')
    return enqueue('spectrum_model', record('analysis', report['analysis_id']),
                   dict(calibrated_id=id, **request.model_dump()))


class WeightPlan(BaseModel):
    profile_id: str = Field(max_length=100)
    anchor_id: str = Field(max_length=100)
    max_hours: float = Field(default=24, gt=0, le=48, allow_inf_nan=False)


@router.post('/api/irsa/results/{id}/weight-plan')
def weights(id: str, request: WeightPlan):
    from backend.exposure_weights import weight_plan
    report, profile = record('irsa_result', id), record('irsa_result', request.profile_id)
    if report.get('kind') != 'calibrated' or profile.get('kind') != 'profile' or report['analysis_id'] != profile['analysis_id'] or report['point'] != profile['point']:
        raise HTTPException(422, 'Kalibracja i diagnostyka muszą dotyczyć tego samego punktu i analizy.')
    try:
        return save_report(weight_plan(report, profile, request.anchor_id, request.max_hours))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.post('/api/irsa/results/{id}/stack-weight-plan')
def stack_weights(id: str):
    from backend.temporal import product
    report = record('irsa_result', id)
    if report.get('kind') != 'weight_plan' or report.get('status') != 'exploratory':
        raise HTTPException(422, 'Brak planu z co najmniej dwiema zgodnymi ekspozycjami.')
    try:
        return product(record('analysis', report['analysis_id']), report['frame_ids'],
                       [w*100 for w in report['weights']], 'stack', report['max_hours'])
    except (ValueError, OSError) as exc:
        raise HTTPException(422, str(exc)) from exc


class Review(BaseModel):
    reviewer: str = Field(min_length=3, max_length=100, pattern=r'\S')
    reason: str = Field(min_length=3, max_length=2000, pattern=r'\S')


@router.post('/api/artifacts/labels/{id}/review')
def review_label(id: str, request: Review):
    record('quality_label', id)
    if len(request.reviewer.strip()) < 3 or len(request.reason.strip()) < 3:
        raise HTTPException(422, 'Podaj recenzenta i uzasadnienie przeglądu.')
    value = dict(label_id=id, **request.model_dump(), reviewed_at=datetime.now(timezone.utc).isoformat())
    store.put('label_review', id, value)
    return value


@router.get('/api/artifacts/status')
def artifact_status():
    from backend.artifact_model import readiness
    return readiness()


@router.get('/api/artifacts/dataset')
def artifact_dataset():
    from backend.artifact_model import dataset
    return dict(schema='artifact-dataset-1', examples=dataset())


@router.post('/api/artifacts/train', status_code=202)
def artifact_train():
    return enqueue('artifact_training', None, {})


@router.get('/api/artifacts/models/{id}')
def artifact_model(id: str):
    return record('artifact_model', id)
