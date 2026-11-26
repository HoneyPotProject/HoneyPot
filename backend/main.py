# FastAPI application entry point (engine disconnected for now).

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import attackers, auth, detectors, events, health, statistics, system
from backend.api.websockets import events as ws_events
from backend.config import settings
from backend.database.connection import init_db
from backend.middleware.rate_limit import RateLimitMiddleware

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info('=== Backend Starting ===')
    await init_db()
    logger.info('=== Backend Ready on port %d ===', settings.MANAGEMENT_PORT)
    yield
    logger.info('=== Shutdown complete ===')


app = FastAPI(
    title='Honeypot Management API',
    description='REST API and WebSocket for the Python Modular Honeypot',
    version='1.0.0',
    lifespan=lifespan,
    docs_url='/api/docs',
    redoc_url='/api/redoc',
)

app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type', 'X-API-Key'],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(attackers.router)
app.include_router(statistics.router)
app.include_router(detectors.router)
app.include_router(system.router)
app.include_router(ws_events.router)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'backend.main:app',
        host=settings.MANAGEMENT_HOST,
        port=settings.MANAGEMENT_PORT,
        reload=False,
    )