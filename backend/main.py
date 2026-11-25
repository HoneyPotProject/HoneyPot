# FastAPI application entry point.
# Creates the app, registers routers, sets CORS,
# and starts the engine + honeypot as background tasks.

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import attackers, auth, detectors, events, health, statistics, system
from backend.api.websockets import events as ws_events
from backend.config import settings
from backend.database.connection import AsyncSessionLocal, init_db
from backend.integration.engine_adapter import EngineAdapter
from backend.middleware.rate_limit import RateLimitMiddleware
from engine.collectors.request_collector import RequestCollector
from engine.core.config import DEFAULT_CONFIG
from engine.core.engine import DetectionEngine
from engine.detectors.brute_force import BruteForceDetector
from engine.detectors.command_injection import CommandInjectionDetector
from engine.detectors.directory_enum import DirectoryEnumerationDetector
from engine.detectors.endpoint_enum import EndpointEnumerationDetector
from engine.detectors.path_traversal import PathTraversalDetector
from engine.detectors.sql_injection import SQLInjectionDetector
from engine.detectors.suspicious_request import SuspiciousRequestDetector
from engine.detectors.xss import XSSDetector
from engine.events.event_processor import EventProcessor
from engine.network.connection_monitor import ConnectionMonitor
from engine.server.http_server import HoneypotHTTPServer
from engine.server.request_handler import RequestHandler

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

detection_engine = DetectionEngine()
engine_adapter = EngineAdapter(queue_size=settings.EVENT_QUEUE_SIZE)
_honeypot_server: HoneypotHTTPServer | None = None
_connection_monitor: ConnectionMonitor | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _honeypot_server, _connection_monitor

    logger.info('=== Honeypot Backend Starting ===')
    await init_db()
    sink = engine_adapter.start(AsyncSessionLocal)

    detection_engine.register(SQLInjectionDetector())
    detection_engine.register(XSSDetector())
    detection_engine.register(PathTraversalDetector())
    detection_engine.register(CommandInjectionDetector())
    detection_engine.register(DirectoryEnumerationDetector())
    detection_engine.register(EndpointEnumerationDetector())
    detection_engine.register(BruteForceDetector())
    detection_engine.register(SuspiciousRequestDetector())
    logger.info('Registered %d detectors', len(detection_engine.detectors))

    collector = RequestCollector(DEFAULT_CONFIG)
    processor = EventProcessor(sink)
    handler = RequestHandler(collector, detection_engine, processor)

    _honeypot_server = HoneypotHTTPServer(
        handler,
        host=settings.HONEYPOT_HOST,
        port=settings.HONEYPOT_PORT,
    )
    await _honeypot_server.start()
    detection_engine.mark_running(True)

    if settings.ENABLE_DECOY_PORTS:
        _connection_monitor = ConnectionMonitor(processor, host=settings.HONEYPOT_HOST)
        await _connection_monitor.start()

    logger.info('=== Backend Ready — Management API on port %d ===', settings.MANAGEMENT_PORT)
    yield

    logger.info('=== Honeypot Backend Shutting Down ===')
    detection_engine.mark_running(False)
    if _connection_monitor:
        await _connection_monitor.stop()
    if _honeypot_server:
        await _honeypot_server.stop()
    await engine_adapter.stop()
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
