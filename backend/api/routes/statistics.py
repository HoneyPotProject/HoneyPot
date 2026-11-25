# GET /api/statistics, /timeline, /top-targets — real database counts only.

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db, require_auth
from backend.database.repository import EventRepository, SourceRepository

router = APIRouter()


@router.get('/api/statistics', tags=['Statistics'])
async def get_statistics(
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    """
    Top-level summary statistics.
    All numbers come from real database counts — nothing is hardcoded.
    """
    total = await EventRepository.count_total(db)
    unique = await SourceRepository.count_unique_ips(db)
    by_severity = await EventRepository.count_by_severity(db)
    by_category = await EventRepository.count_by_category(db)
    last_24h = await EventRepository.count_last_24h(db)
    high_sev = by_severity.get('high', 0)
    critical = by_severity.get('critical', 0)

    enabled = 0
    try:
        from backend.main import detection_engine
        enabled = len([d for d in detection_engine.detectors if getattr(d, 'enabled', True)])
    except Exception:
        pass

    return {
        'total_events': total,
        'unique_sources': unique,
        'critical_events': critical,
        'high_severity_events': high_sev,
        'events_last_24h': last_24h,
        'enabled_detectors': enabled,
        'category_distribution': by_category,
        'severity_distribution': by_severity,
    }


@router.get('/api/statistics/attacks', tags=['Statistics'])
async def get_attack_stats(
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    by_category = await EventRepository.count_by_category(db)
    return {'category_distribution': by_category}


@router.get('/api/statistics/severity', tags=['Statistics'])
async def get_severity_stats(
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    by_severity = await EventRepository.count_by_severity(db)
    return {'severity_distribution': by_severity}


@router.get('/api/statistics/timeline', tags=['Statistics'])
async def get_timeline(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    """Event counts bucketed by hour for the timeline chart."""
    data = await EventRepository.timeline(db, hours=hours)
    return {'timeline': data}


@router.get('/api/statistics/top-targets', tags=['Statistics'])
async def get_top_targets(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    """Most frequently targeted paths."""
    rows = await EventRepository.top_targets(db, limit=limit)
    return {'top_targets': [{'path': r[0], 'count': r[1]} for r in rows]}


@router.get('/api/statistics/top-sources', tags=['Statistics'])
async def get_top_sources(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    rows = await EventRepository.top_sources(db, limit=limit)
    return {'top_sources': [{'source_ip': r[0], 'count': r[1]} for r in rows]}


@router.get('/api/statistics/hourly', tags=['Statistics'])
async def get_hourly(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
    _auth=Depends(require_auth),
):
    return {'hourly': await EventRepository.hourly_activity(db, hours=hours)}
