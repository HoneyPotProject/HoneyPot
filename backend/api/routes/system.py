# GET /api/system/status and /api/system/metrics — actual component checks.

from fastapi import APIRouter, Depends

from backend.api.dependencies import require_auth
from backend.config import settings

router = APIRouter()


async def _collect_status() -> dict:
    from backend.main import detection_engine, engine_adapter, _honeypot_server
    from backend.services.ws_manager import ws_manager

    db_status = 'error'
    try:
        from backend.database.connection import engine as db_engine
        from sqlalchemy import text
        async with db_engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        db_status = 'ok'
    except Exception:
        db_status = 'error'

    engine_running = bool(getattr(detection_engine, 'running', False))
    honeypot_running = bool(_honeypot_server and _honeypot_server.running)

    return {
        'backend_status': 'healthy',
        'engine_running': engine_running and honeypot_running,
        'honeypot_running': honeypot_running,
        'database_status': db_status,
        'queue_depth': engine_adapter.queue_depth,
        'queue_capacity': engine_adapter.queue_capacity,
        'processed_events': engine_adapter.processed_events,
        'dropped_events': engine_adapter.dropped_events,
        'processing_errors': engine_adapter.processing_errors,
        'last_processed_event': engine_adapter.last_processed_event,
        'ws_connections': ws_manager.connection_count,
        'uptime_seconds': engine_adapter.uptime_seconds,
        'honeypot_port': settings.HONEYPOT_PORT,
    }


@router.get('/api/system/status', tags=['System'])
async def system_status(_auth=Depends(require_auth)):
    return await _collect_status()


@router.get('/api/system/metrics', tags=['System'])
async def system_metrics(_auth=Depends(require_auth)):
    status = await _collect_status()
    status['queue_utilization'] = (
        round(status['queue_depth'] / status['queue_capacity'], 4)
        if status['queue_capacity']
        else 0
    )
    return status
