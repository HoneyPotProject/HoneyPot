# GET /api/events, GET /api/events/{event_id}, POST annotation.

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db, require_auth
from backend.database.repository import EventRepository
from backend.database.models import AnalystAnnotationModel

router = APIRouter()


def _decode_event(row) -> dict:
    """Decode JSON text columns back to Python objects before returning."""
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
    source_ip: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    attack_category: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    """List security events with optional filtering and pagination."""
    rows, total = await EventRepository.list_events(
        db, page=page, page_size=page_size,
        source_ip=source_ip, severity=severity,
        attack_category=attack_category,
        start_time=start_time, end_time=end_time,
        search=search,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return {
        'events': [_decode_event(r) for r in rows],
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    }


@router.get('/api/events/{event_id}', tags=['Events'])
async def get_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    """Get a single event by its UUID."""
    row = await EventRepository.get_by_event_id(db, event_id)
    if not row:
        raise HTTPException(status_code=404, detail='Event not found')
    return _decode_event(row)


@router.post('/api/events/{event_id}/annotation', tags=['Events'])
async def add_annotation(
    event_id: str,
    status: str = 'new',
    notes: Optional[str] = None,
    analyst_id: str = 'analyst',
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    """Add an analyst annotation to a security event."""
    event = await EventRepository.get_by_event_id(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail='Event not found')

    annotation = AnalystAnnotationModel(
        event_id=event_id,
        analyst_id=analyst_id,
        status=status,
        notes=notes,
    )
    db.add(annotation)
    await db.flush()
    return {'status': 'created', 'annotation_id': annotation.id}
