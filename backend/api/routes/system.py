# GET /api/system/status — overall system health and queue metrics.

from fastapi import APIRouter, Depends

from backend.api.dependencies import require_auth

router = APIRouter()


@router.get('/api/system/status', tags=['System'])
async def system_status(_auth=Depends(require_auth)):
    """Return engine status, queue depth, WebSocket connections, and error counts."""
    from backend.main import engine_adapter
    from backend.services.ws_manager import ws_manager

    # Check database connectivity.
    db_status = 'ok'
    try:
        from backend.database.connection import engine as db_engine
        from sqlalchemy import text
        async with db_engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
    except Exception:
        db_status = 'error'

    return {
        'backend_status': 'healthy',
        'engine_running': True,
        'database_status': db_status,
        'queue_depth': engine_adapter.queue_depth,
        'queue_capacity': engine_adapter._queue_size,
        'ws_connections': ws_manager.connection_count,
        'dropped_events': engine_adapter.dropped_events,
        'processing_errors': engine_adapter.processing_errors,
        'uptime_seconds': engine_adapter.uptime_seconds,
    }
