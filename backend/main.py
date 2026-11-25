# FastAPI application entry point.
# Creates the app, registers routers, sets CORS,
# and starts the engine + honeypot as background tasks.

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database.connection import init_db, AsyncSessionLocal
from backend.integration.engine_adapter import EngineAdapter

# --- Engine imports ---
# These are the ONLY engine modules the backend imports directly.
# The engine never imports from the backend.
from engine.core.engine import DetectionEngine
from engine.core.config import DEFAULT_CONFIG
from engine.collectors.request_collector import RequestCollector
from engine.events.event_processor import EventProcessor
from engine.server.request_handler import RequestHandler
from engine.server.http_server import HoneypotHTTPServer

# --- Detector imports ---
from engine.detectors.sql_injection import SQLInjectionDetector
from engine.detectors.xss import XSSDetector
from engine.detectors.path_traversal import PathTraversalDetector
from engine.detectors.command_injection import CommandInjectionDetector
from engine.detectors.directory_enum import DirectoryEnumerationDetector
from engine.detectors.endpoint_enum import EndpointEnumerationDetector
from engine.detectors.brute_force import BruteForceDetector
from engine.detectors.suspicious_request import SuspiciousRequestDetector

# --- Route imports ---
from backend.api.routes import health, events, attackers, statistics, detectors, system
from backend.api.websockets import events as ws_events

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global singletons — created once at startup and shared across requests.
# Routes that need these import them lazily (inside the route function)
# to prevent circular imports at module level.
# ---------------------------------------------------------------------------

# The detection engine with all detectors registered.
detection_engine = DetectionEngine()

# The adapter that owns the in-memory queue and the worker task.
engine_adapter = EngineAdapter(queue_size=settings.EVENT_QUEUE_SIZE)

# Reference to the honeypot server (kept for clean shutdown).
_honeypot_server: HoneypotHTTPServer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.

    Startup order:
      1. Create database tables.
      2. Start the EngineAdapter (queue + worker task).
      3. Register all detectors.
      4. Build the detection pipeline.
      5. Start the honeypot HTTP listener on HONEYPOT_PORT.

    Shutdown:
      1. Stop the honeypot listener.
      2. Stop the engine adapter (drain queue, cancel worker).
    """
    global _honeypot_server

    logger.info('=== Honeypot Backend Starting ===')

    # 1. Initialize the database (creates tables if they don't exist).
    await init_db()

    # 2. Start the engine adapter: creates the bounded asyncio.Queue
    #    and launches the worker task that drains it to the database.
    #    Returns the BackendEventSink the EventProcessor will call.
    sink = engine_adapter.start(AsyncSessionLocal)

    # 3. Register all detectors with the engine.
    #    Order doesn't matter — they all run independently per request.
    detection_engine.register(SQLInjectionDetector())
    detection_engine.register(XSSDetector())
    detection_engine.register(PathTraversalDetector())
    detection_engine.register(CommandInjectionDetector())
    detection_engine.register(DirectoryEnumerationDetector())
    detection_engine.register(EndpointEnumerationDetector())
    detection_engine.register(BruteForceDetector())
    detection_engine.register(SuspiciousRequestDetector())

    logger.info('Registered %d detectors', len(detection_engine.detectors))

    # 4. Build the detection pipeline (dependency chain):
    #    RequestCollector   — raw bytes -> RequestContext
    #    RequestHandler     — wires collector + engine + processor + simulator
    #    EventProcessor     — results -> SecurityEvent -> sink.save()
    #    BackendEventSink   — sink.save() -> queue.put_nowait()
    #    EventWorker        — queue.get() -> EventService -> DB + WS broadcast
    collector = RequestCollector(DEFAULT_CONFIG)
    processor = EventProcessor(sink)
    handler = RequestHandler(collector, detection_engine, processor)

    # 5. Start the decoy HTTP listener.
    _honeypot_server = HoneypotHTTPServer(handler, port=settings.HONEYPOT_PORT)
    await _honeypot_server.start()

    logger.info('=== Backend Ready — Management API on port %d ===', settings.MANAGEMENT_PORT)

    yield  # FastAPI serves requests here.

    # --- Shutdown ---
    logger.info('=== Honeypot Backend Shutting Down ===')
    if _honeypot_server:
        await _honeypot_server.stop()
    await engine_adapter.stop()
    logger.info('=== Shutdown complete ===')


# ---------------------------------------------------------------------------
# Create the FastAPI application.
# ---------------------------------------------------------------------------

app = FastAPI(
    title='Honeypot Management API',
    description='REST API and WebSocket for the Python Modular Honeypot',
    version='1.0.0',
    lifespan=lifespan,
    docs_url='/api/docs',
    redoc_url='/api/redoc',
)

# CORS — allow the Vite dev server and configured origins to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Register all API routes.
app.include_router(health.router)
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
        host='127.0.0.1',
        port=settings.MANAGEMENT_PORT,
        reload=False,
    )
