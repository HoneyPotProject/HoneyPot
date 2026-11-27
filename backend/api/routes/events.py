# GET /api/events, GET /api/events/{event_id}, export, annotations.

import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db, require_auth
from backend.database.models import AnalystAnnotationModel
from backend.database.repository import EventRepository
from backend.schemas.event import AnnotationIn

router = APIRouter()

ALLOWED_STATUSES = {'new', 'under_review', 'reviewed', 'false_positive'}


def _decode_event(row) -> dict:
    return {
        'event_id': row.event_id,
        'source_ip': row.source_ip,
        'timestamp': row.timestamp,
        'attack_category': row.attack_category,
        'severity': row.severity,
        'confidence': row.confidence,
        'detector_names': json.loads(row.detector_names or '[]'),
        'detection_reasons': json.loads(row.detection_reasons or '[]'),
        'evidence': json.loads(row.evidence or '{}'),
        'target': row.target,
        'method': row.method,
        'path': row.path,
        'request_id': row.request_id,
        'metadata': json.loads(row.metadata_json or '{}'),
    }


@router.get('/api/events', tags=['Events'])
async def list_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    source_ip: str | None = Query(None),
    severity: str | None = Query(None),
    attack_category: str | None = Query(None),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query('timestamp'),
    sort_dir: str = Query('desc'),
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    rows, total = await EventRepository.list_events(
        db, page=page, page_size=page_size,
        source_ip=source_ip, severity=severity,
        attack_category=attack_category,
        start_time=start_time, end_time=end_time,
        search=search, sort_by=sort_by, sort_dir=sort_dir,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        'events': [_decode_event(r) for r in rows],
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    }


@router.get('/api/events/export', tags=['Events'])
async def export_events(
    source_ip: str | None = Query(None),
    severity: str | None = Query(None),
    attack_category: str | None = Query(None),
    start_time: datetime | None = Query(None),
    end_time: datetime | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    rows, _total = await EventRepository.list_events(
        db, page=1, page_size=200,
        source_ip=source_ip, severity=severity,
        attack_category=attack_category,
        start_time=start_time, end_time=end_time,
        search=search,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([
        'event_id', 'timestamp', 'source_ip', 'attack_category', 'severity',
        'confidence', 'method', 'path', 'reasons',
    ])
    for row in rows:
        writer.writerow([
            row.event_id, row.timestamp, row.source_ip, row.attack_category,
            row.severity, row.confidence, row.method, row.path, row.detection_reasons,
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=events.csv'},
    )


@router.get('/api/events/{event_id}', tags=['Events'])
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    row = await EventRepository.get_by_event_id(db, event_id)
    if not row:
        raise HTTPException(status_code=404, detail='Event not found')
    payload = _decode_event(row)
    related = await EventRepository.related_events(db, row.source_ip, row.event_id)
    payload['related_events'] = [
        {
            'event_id': r.event_id,
            'timestamp': r.timestamp,
            'attack_category': r.attack_category,
            'severity': r.severity,
            'path': r.path,
        }
        for r in related
    ]
    annotations = [
        {
            'id': a.id,
            'status': a.status,
            'notes': a.notes,
            'analyst_id': a.analyst_id,
            'created_at': a.created_at,
            'updated_at': a.updated_at,
        }
        for a in (row.annotations or [])
    ]
    payload['annotations'] = annotations
    payload['investigation_status'] = annotations[-1]['status'] if annotations else 'new'
    return payload


@router.post('/api/events/{event_id}/annotation', tags=['Events'])
async def add_annotation(
    event_id: str,
    body: AnnotationIn,
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    event = await EventRepository.get_by_event_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found')
    if body.status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail='Invalid investigation status')

    annotation = AnalystAnnotationModel(
        event_id=event_id,
        analyst_id=body.analyst_id,
        status=body.status,
        notes=body.notes,
    )
    db.add(annotation)
    await db.flush()
    return {'status': 'created', 'annotation_id': annotation.id}
