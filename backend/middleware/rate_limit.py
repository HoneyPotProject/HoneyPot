from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in {'/api/health', '/api/docs', '/api/redoc', '/openapi.json'}:
            return await call_next(request)
        if not path.startswith('/api') and not path.startswith('/ws'):
            return await call_next(request)

        host = request.client.host if request.client else 'unknown'
        now = time.time()
        limit = settings.API_RATE_LIMIT_PER_MINUTE
        if path.startswith('/api/auth/login'):
            limit = settings.AUTH_RATE_LIMIT_PER_MINUTE
        window = 60.0
        bucket = self._hits[f'{host}:{path.split("?")[0]}']
        while bucket and now - bucket[0] > window:
            bucket.popleft()
        if len(bucket) >= limit:
            return JSONResponse({'detail': 'Rate limit exceeded'}, status_code=429)
        bucket.append(now)
        return await call_next(request)
