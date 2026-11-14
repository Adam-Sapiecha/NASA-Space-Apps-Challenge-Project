"""Prepare requested observations in an immutable, shared comparison workspace."""
import json
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend import store
from backend.science import build_analysis

router = APIRouter()
MAX_READY_FRAMES = 48


class ComparisonRequest(BaseModel):
    observation_ids: list[str] = Field(min_length=1, max_length=12)
    previous_ids: list[str] = Field(default_factory=list, max_length=2)


def workspace_plan(parent, requested, previous_ids=()):
    loaded = [frame['id'] for frame in parent['frames']]
    prior = parent.get('workspace', {})
    recommended = [id for id in (prior.get('recommended_ids') or (parent.get('selection') or {}).get('selected_ids') or loaded[:2]) if id in loaded]
    if not recommended:
        recommended = loaded[:2]
    pair = [id for id in (prior.get('recommended_pair_ids') or (parent.get('selection') or {}).get('pair_ids') or recommended[:2]) if id in loaded]
    if len(pair) != 2:
        pair = [recommended[0], recommended[-1]]
    # Retain the recommended set and every requested frame. The cache bounds
    # memory; it does not restrict which archive observations can be requested.
    mandatory = list(dict.fromkeys([*recommended, *requested, *previous_ids]))
    order = [id for id in prior.get('cache_order', loaded) if id in loaded and id not in requested]
    order.extend(dict.fromkeys(requested))
    retained = list(dict.fromkeys([*mandatory, *reversed(order)]))[:MAX_READY_FRAMES]
    return retained, dict(root_analysis_id=prior.get('root_analysis_id', parent['id']),
                         recommended_ids=recommended, recommended_pair_ids=pair,
                         requested_ids=requested, cache_order=[id for id in order if id in retained],
                         available_observations=len(parent['search']['observations']))


def prepare_comparison(id, parent, requested, previous_ids=()):
    retained, workspace = workspace_plan(parent, requested, previous_ids)
    build_analysis(id, parent['search'], retained, previous=parent,
                   selection=parent.get('selection'), workspace=workspace)


@router.post('/api/analyses/{id}/comparison', status_code=202)
def comparison(id: str, request: ComparisonRequest):
    from backend.main import record, submit_job
    parent = record('analysis', id)
    available = {row['id'] for row in parent['search']['observations']}
    if not set([*request.observation_ids, *request.previous_ids]) <= available:
        raise HTTPException(422, 'Wybierz obserwacje z tego samego pola.')
    if parent.get('workspace') and set(request.observation_ids) <= {frame['id'] for frame in parent['frames']}:
        return dict(analysis_id=id, status='ready')
    with store.connect() as db:
        active = sum(json.loads(row[0])['status'] in ('queued', 'running')
                     for row in db.execute("SELECT body FROM records WHERE kind='job'"))
    if active >= 3:
        raise HTTPException(429, 'Kolejka jest pełna. Poczekaj na zakończenie analizy.')
    job_id = uuid.uuid4().hex
    store.put('job', job_id, dict(id=job_id, status='queued', completed=0,
                                 total=len(set(request.observation_ids)), phase='comparison',
                                 message='Przygotowuję wybrane daty i pasma…'))
    submit_job(job_id, prepare_comparison, parent, request.observation_ids, request.previous_ids)
    return dict(id=job_id, status='queued')
