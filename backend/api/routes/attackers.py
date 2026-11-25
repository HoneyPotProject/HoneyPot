# GET /api/attackers, GET /api/attackers/{ip}, GET /api/attackers/{ip}/events.

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db, require_auth
from backend.database.repository import SourceRepository, EventRepository

router = APIRouter()


def _decode_source(row) -> dict:
    return {
        'source_ip': row.source_ip,
        'first_seen': row.first_seen,
        'last_seen': row.last_seen,
        'total_events': row.total_events,
        'last_category': row.last_category,
        'category_counts': json.loads(row.category_counts or '{}'),
        'severity_counts': json.loads(row.severity_counts or '{}'),
    }


@router.get('/api/attackers', tags=['Sources'])
async def list_attackers(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    """List all observed source IPs with their aggregated stats."""
    rows, total = await SourceRepository.list_sources(db, page=page, page_size=page_size)
    return {
        'sources': [_decode_source(r) for r in rows],
        'total': total,
        'page': page,
        'page_size': page_size,
    }


@router.get('/api/attackers/{source_ip}', tags=['Sources'])
async def get_attacker(
    source_ip: str,
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    """Get aggregated stats for a specific source IP."""
    row = await SourceRepository.get_by_ip(db, source_ip)
    if not row:
        raise HTTPException(status_code=404, detail='Source IP not found')
    return _decode_source(row)


@router.get('/api/attackers/{source_ip}/events', tags=['Sources'])
async def get_attacker_events(
    source_ip: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    """List all events from a specific source IP."""
    rows, total = await EventRepository.list_events(
        db, page=page, page_size=page_size, source_ip=source_ip
    )
    events = []
    for r in rows:
        events.append({
            'event_id': r.event_id,
            'timestamp': r.timestamp,
            'attack_category': r.attack_category,
            'severity': r.severity,
            'path': r.path,
            'method': r.method,
        })
    return {'events': events, 'total': total, 'page': page, 'page_size': page_size}


@router.get('/api/attackers/{source_ip}/timeline', tags=['Sources'])
async def get_attacker_timeline(
    source_ip: str,
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    row = await SourceRepository.get_by_ip(db, source_ip)
    if not row:
        raise HTTPException(status_code=404, detail='Source IP not found')
    data = await EventRepository.timeline(db, hours=hours, source_ip=source_ip)
    return {'source_ip': source_ip, 'timeline': data}
