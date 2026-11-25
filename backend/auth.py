# API key check for management endpoints.
# Clients send: X-API-Key: <key-from-.env>

import logging
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from backend.config import settings

logger = logging.getLogger(__name__)

# FastAPI reads this header automatically when used as a dependency.
api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)


async def require_auth(api_key: str = Security(api_key_header)) -> str:
    """
    FastAPI dependency that enforces API key authentication.

    Usage in a route:
        @router.get('/protected')
        async def route(user=Depends(require_auth)):
            ...

    Returns the API key string on success.
    Raises HTTP 401 on failure.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Missing X-API-Key header',
        )
    if api_key != settings.API_KEY:
        logger.warning('Invalid API key attempt')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid API key',
        )
    return api_key
