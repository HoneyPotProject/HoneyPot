# GET /api/health — liveness check (always returns 200 if process is up).

from fastapi import APIRouter

router = APIRouter()


@router.get('/api/health', tags=['Health'])
async def health_check():
    """
    Liveness probe.
    Returns 200 if the FastAPI process is running.
    Does NOT require authentication (safe to expose publicly).
    """
    return {'status': 'ok', 'service': 'honeypot-backend'}
