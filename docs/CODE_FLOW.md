# CODE FLOW — Python Honeypot

**Purpose:** One document that maps every file to its exact role in the data pipeline. Read this to understand how a suspicious HTTP request travels from arrival at the decoy port all the way to the React dashboard.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Complete Data Flow Diagram](#2-complete-data-flow-diagram)
3. [Layer 1 — Decoy Listener (Engine Server)](#3-layer-1--decoy-listener)
4. [Layer 2 — Detection Engine (Engine Core + Detectors)](#4-layer-2--detection-engine)
5. [Layer 3 — Event Processing (Engine Events)](#5-layer-3--event-processing)
6. [Layer 4 — Integration Bridge](#6-layer-4--integration-bridge)
7. [Layer 5 — Backend Persistence (FastAPI + SQLite)](#7-layer-5--backend-persistence)
8. [Layer 6 — REST API](#8-layer-6--rest-api)
9. [Layer 7 — WebSocket](#9-layer-7--websocket)
10. [Layer 8 — React Frontend](#10-layer-8--react-frontend)
11. [File Reference Table](#11-file-reference-table)
12. [Data Object Reference](#12-data-object-reference)
13. [Dependency Rules](#13-dependency-rules)
14. [Port Reference](#14-port-reference)
15. [Startup Sequence](#15-startup-sequence)

---

## 1. System Overview

```
  UNTRUSTED INTERNET
         │
         ▼  port 8080 (decoy)
  ┌──────────────────────────────────────────────────────────┐
  │            Python Process (single process)               │
  │                                                          │
  │  HoneypotHTTPServer  ──► RequestHandler                  │
  │                              │                           │
  │                      RequestCollector                    │
  │                              │ RequestContext            │
  │                      DetectionEngine                     │
  │                              │ [DetectionResult, ...]    │
  │                      EventProcessor                      │
  │                              │ SecurityEvent             │
  │                      BackendEventSink                    │
  │                              │                           │
  │                      asyncio.Queue                       │
  │                              │                           │
  │                      EventWorker (task)                  │
  │                              │ dict                      │
  │                      EventService                        │
  │                         /        \                       │
  │                        /          \                      │
  │               Repository        ws_manager               │
  │                   │                 │                    │
  │                SQLite        WebSocket clients           │
  │                                                          │
  │  FastAPI (Uvicorn)  ◄─── port 8000 (management)         │
  │    REST API ──────────────────────────────────► Browser  │
  │    WebSocket ──────────────────────────────────► Browser │
  └──────────────────────────────────────────────────────────┘
         ▲
  BROWSER/VITE  port 5173 (React dev server)
```

---

## 2. Complete Data Flow Diagram

```
Raw TCP bytes arrive at port 8080
         │
         ▼
engine/server/http_server.py
  HoneypotHTTPServer.start()
  → asyncio.start_server(handler.handle, port=8080)
         │
         ▼
engine/server/request_handler.py
  RequestHandler.handle(reader, writer)
  → Reads up to 64 KB with 10s timeout
         │
         ▼
engine/collectors/request_collector.py
  RequestCollector.collect(raw_bytes, source_ip, source_port)
  → Validates IP with ipaddress module
  → Parses HTTP request line (method, path)
  → URL-decodes path and query params
  → Redacts Authorization, Cookie, password headers
  → Truncates body to 8 KB
  → Returns RequestContext (frozen dataclass, immutable)
         │
         ▼  RequestContext
engine/core/engine.py
  DetectionEngine.analyze(ctx)
  → For each registered detector:
      try:
        results = detector.analyze(ctx)   ← each returns list[DetectionResult]
      except:
        log and continue                   ← one crash never stops others
  → Returns flat list of all DetectionResult objects
         │
  Detectors called:                        (each is independent)
  ├── engine/detectors/sql_injection.py    SQLInjectionDetector
  ├── engine/detectors/xss.py             XSSDetector
  ├── engine/detectors/path_traversal.py  PathTraversalDetector
  ├── engine/detectors/command_injection.py CommandInjectionDetector
  ├── engine/detectors/directory_enum.py  DirectoryEnumerationDetector
  ├── engine/detectors/endpoint_enum.py   EndpointEnumerationDetector (stateful)
  ├── engine/detectors/brute_force.py     BruteForceDetector (stateful)
  └── engine/detectors/suspicious_request.py SuspiciousRequestDetector
  All detectors import patterns from:
  └── engine/rules/signatures.py          Compiled regexes and sensitive paths
         │
         ▼  list[DetectionResult]
engine/events/event_processor.py
  EventProcessor.process(ctx, results)
  → If results is empty → return None (normal request, no event)
  → Run analyzers:
      engine/analyzers/behavior.py         BehaviorAnalyzer.score(ip)
      engine/analyzers/automation.py       AutomationAnalyzer.likelihood(ip, ua)
      engine/analyzers/session_analyzer.py SessionAnalyzer.process(ip, cookie)
  → Pick dominant category (highest severity detector wins)
  → Average confidence across all results
  → Collect all reasons and evidence
  → Build SecurityEvent (uuid4 ID, all fields merged)
  → Call sink.save(event)                  ← THE INTEGRATION BOUNDARY
         │
         ▼  SecurityEvent
engine/events/storage_interface.py
  EventSink.save(event)                    ← abstract method
         │
         ▼  (concrete implementation in backend)
backend/integration/event_sink.py
  BackendEventSink.save(event)
  → queue.put_nowait(event)
  → If QueueFull: increment dropped counter, log warning, return
  → Never raises (engine must keep running)
         │
         ▼  SecurityEvent in queue
backend/integration/engine_adapter.py
  EngineAdapter._worker_loop()             ← asyncio.Task running continuously
  → queue.get() waits for next event
  → event_mapper.to_db_dict(event)         ← converts engine object to plain dict
         │
         ▼  dict
backend/services/event_service.py
  EventService.persist_and_broadcast(event_dict)
  ├── EventRepository.create(session, event_dict)    ← INSERT into SQLite
  ├── SourceRepository.upsert(session, ip, event)    ← UPDATE per-IP aggregates
  ├── session.commit()
  └── ws_manager.broadcast(ws_payload)              ← send to all WebSocket clients
         │
         ├──► data/database/honeypot.db (SQLite)
         │        tables: security_events, source_observations,
         │                analyst_annotations, audit_log
         │
         └──► WebSocket clients (browsers)
                  ↓ JSON message:
                  {"type": "security_event", "data": {...}}
```

---

## 3. Layer 1 — Decoy Listener

**Location:** `engine/server/`

| File | Class | What it does |
|------|-------|-------------|
| `http_server.py` | `HoneypotHTTPServer` | Opens the decoy TCP port (8080) with `asyncio.start_server`. Applies read size limit and timeout. Entry point for all untrusted traffic. |
| `request_handler.py` | `RequestHandler` | Callback for every connection. Reads bytes → calls collector → runs engine → runs processor → sends fake response. |
| `response_simulator.py` | *(functions)* | Pre-built byte strings for fake login page, fake admin, fake 404. Never reads from disk. Never executes request data. |

**Key design rule:** The decoy listener is completely isolated from the management API. Port 8080 never serves management endpoints.

---

## 4. Layer 2 — Detection Engine

**Location:** `engine/core/`, `engine/detectors/`, `engine/rules/`

| File | Class | What it does |
|------|-------|-------------|
| `core/config.py` | `EngineConfig` | Central numeric settings: body limit, time windows, thresholds. Imported by detectors. Never scattered as magic numbers. |
| `core/context.py` | `RequestContext` | **Frozen** (immutable) dataclass. All detectors receive exactly this — nothing else. Source IP, method, path, query params, redacted headers, truncated body, timestamp, request ID. |
| `core/detection.py` | `DetectionResult`, `Severity`, `AttackCategory` | What one detector returns. Enums define all valid severities and categories. |
| `core/engine.py` | `DetectionEngine` | Runs every registered detector. Each is wrapped in try/except. Returns flat list. |
| `detectors/base.py` | `BaseDetector` | Abstract base class. All detectors implement `analyze(ctx) -> list[DetectionResult]`. |
| `detectors/sql_injection.py` | `SQLInjectionDetector` | Multi-round URL decode, then regex match from `signatures.py`. |
| `detectors/xss.py` | `XSSDetector` | Script tags, event handlers, javascript: URLs including encoded forms. |
| `detectors/path_traversal.py` | `PathTraversalDetector` | `../`, `..\`, single/double/unicode-encoded forms. |
| `detectors/command_injection.py` | `CommandInjectionDetector` | Shell separators + command words. Never executes. |
| `detectors/directory_enum.py` | `DirectoryEnumerationDetector` | Exact + prefix match against `SENSITIVE_PATHS`. Stateless. |
| `detectors/endpoint_enum.py` | `EndpointEnumerationDetector` | Sliding window per IP. Stateful (in-memory deque). |
| `detectors/brute_force.py` | `BruteForceDetector` | Counts POST /login per IP in sliding window. Stateful. |
| `detectors/suspicious_request.py` | `SuspiciousRequestDetector` | Unusual methods, missing Host, oversized headers. Low confidence. |
| `rules/signatures.py` | *(constants)* | All compiled regexes and path lists. Detectors import from here. Tune rules here, never in detector logic. |

**Adding a new detector:** Create a file in `engine/detectors/`, subclass `BaseDetector`, implement `analyze()`, register it in `backend/main.py`. Nothing else needs to change.

---

## 5. Layer 3 — Event Processing

**Location:** `engine/events/`, `engine/analyzers/`

| File | Class | What it does |
|------|-------|-------------|
| `events/event.py` | `SecurityEvent` | The normalized, complete record of one detected incident. Includes UUID, all classification results, evidence, and metadata. |
| `events/storage_interface.py` | `EventSink` | **The integration boundary.** Abstract class with one method: `async save(event)`. The engine knows only this. |
| `events/event_processor.py` | `EventProcessor` | **Classification happens here and only here.** Merges results from all detectors, runs analyzers, builds `SecurityEvent`, calls `sink.save()`. |
| `analyzers/behavior.py` | `BehaviorAnalyzer` | Per-IP event history. Tracks repeated categories, mixed attack types. Produces threat score (0–1). |
| `analyzers/automation.py` | `AutomationAnalyzer` | Request rate → automation likelihood. User-Agent is a secondary hint only. |
| `analyzers/session_analyzer.py` | `SessionAnalyzer` | Groups requests by IP + time gap + cookie into sessions. |

---

## 6. Layer 4 — Integration Bridge

**Location:** `backend/integration/`

This is where the engine hands events to the backend without either knowing about the other's internal structure.

| File | Class/Function | What it does |
|------|---------------|-------------|
| `event_sink.py` | `BackendEventSink` | Implements `EventSink`. Puts engine events into the bounded `asyncio.Queue`. Drops and counts if queue is full. **Never raises.** |
| `event_mapper.py` | `to_db_dict()` | Converts a `SecurityEvent` dataclass into a plain Python dict the database layer can store. Handles enum `.value` extraction. |
| `engine_adapter.py` | `EngineAdapter` | Owns the `asyncio.Queue` and the worker `asyncio.Task`. On startup: creates queue → creates sink → starts worker. Worker loop: `queue.get()` → `to_db_dict()` → `EventService.persist_and_broadcast()`. |

**Dependency direction:**
```
backend/integration/event_sink.py  ──imports──► engine/events/storage_interface.py
engine/ never imports from backend/
```

**Queue limitation:** The queue is in-memory only. Events in the queue at crash time are lost. This is documented and acceptable for the initial version.

---

## 7. Layer 5 — Backend Persistence

**Location:** `backend/database/`, `backend/services/`

| File | Class | What it does |
|------|-------|-------------|
| `database/connection.py` | `Base`, `engine`, `AsyncSessionLocal`, `get_db()`, `init_db()` | SQLAlchemy async engine (aiosqlite). Session factory. `init_db()` creates tables. `get_db()` is the FastAPI session dependency. |
| `database/models.py` | `SecurityEventModel`, `SourceObservationModel`, `AnalystAnnotationModel`, `AuditLogModel` | SQLAlchemy ORM table definitions. JSON text columns for lists and dicts. |
| `database/repository.py` | `EventRepository`, `SourceRepository` | All database queries: insert, paginated list with filters, aggregations, top targets, timeline, source observation upsert. |
| `services/event_service.py` | `EventService` | Calls repository to save, calls ws_manager to broadcast. If DB save fails → skip broadcast. If broadcast fails → DB is unaffected. |
| `services/ws_manager.py` | `WebSocketManager`, `ws_manager` | Tracks connected WebSocket clients. `broadcast(message)` sends to all, removes dead connections. Single shared instance. |

---

## 8. Layer 6 — REST API

**Location:** `backend/api/routes/`

All routes require `X-API-Key` header authentication (except `/api/health`).

| File | Routes | What it returns |
|------|--------|----------------|
| `health.py` | `GET /api/health` | `{status: 'ok', service: 'honeypot-backend'}` — always 200 if process is up |
| `events.py` | `GET /api/events` `GET /api/events/{id}` `POST /api/events/{id}/annotation` | Paginated event list with filters, single event detail, analyst annotations |
| `attackers.py` | `GET /api/attackers` `GET /api/attackers/{ip}` `GET /api/attackers/{ip}/events` | Per-IP aggregated stats, event history |
| `statistics.py` | `GET /api/statistics` `GET /api/statistics/timeline` `GET /api/statistics/top-targets` | Real database counts, hourly timeline, top paths |
| `detectors.py` | `GET /api/detectors` `GET /api/detectors/{name}` | Live detector list from the running engine |
| `system.py` | `GET /api/system/status` | Queue depth, WS connections, dropped events, uptime |

**Authentication:** `backend/auth.py` — `require_auth` FastAPI dependency checks `X-API-Key` header against `API_KEY` from `.env`.

**Schemas:** `backend/schemas/` — Pydantic v2 models defining request and response shapes.

---

## 9. Layer 7 — WebSocket

**Location:** `backend/api/websockets/events.py`, `backend/services/ws_manager.py`

| Component | What it does |
|-----------|-------------|
| `GET /ws/events?api_key=<key>` | WebSocket endpoint. Authenticates via query param. Registers with `ws_manager`. Sends heartbeat ping every 30s. |
| `ws_manager.broadcast(msg)` | Called by `EventService` after each successful DB write. Sends `{"type": "security_event", "data": {...}}` to all connected clients. |

**Message format:**
```json
{
  "type": "security_event",
  "data": {
    "event_id": "uuid",
    "source_ip": "1.2.3.4",
    "timestamp": "2026-11-25T10:00:00Z",
    "attack_category": "sql_injection",
    "severity": "high",
    "confidence": 0.85,
    "target": "/login",
    "method": "POST",
    "path": "/login",
    "detector_names": ["SQLInjectionDetector"],
    "detection_reasons": ["Suspicious SQL pattern: UNION SELECT"]
  }
}
```

---

## 10. Layer 8 — React Frontend

**Location:** `frontend/src/`

| File/Directory | What it does |
|---------------|-------------|
| `main.jsx` | React root entry point. Mounts `<App />`. |
| `App.jsx` | Router setup. Auth guard wraps protected routes. |
| `services/api.js` | Axios instance with base URL from `VITE_API_BASE_URL` env var. Auth header from stored API key. |
| `services/eventsApi.js` | `getEvents(filters)`, `getEvent(id)` — calls `GET /api/events`. |
| `services/attackersApi.js` | `getAttackers()`, `getAttacker(ip)` — calls `GET /api/attackers`. |
| `services/statisticsApi.js` | `getStatistics()`, `getTimeline()` — calls `GET /api/statistics`. |
| `services/detectorsApi.js` | `getDetectors()` — calls `GET /api/detectors`. |
| `services/systemApi.js` | `getStatus()` — calls `GET /api/system/status`. |
| `services/websocket.js` | Manages native WebSocket to `ws://backend/ws/events?api_key=`. Auto-reconnects. Event emitter pattern. |
| `hooks/useWebSocket.js` | React hook wrapping `websocket.js`. Provides `events`, `connected` state. |
| `hooks/useAuth.js` | Stores API key in sessionStorage. Provides `login()`, `logout()`, `isAuthenticated`. |
| `hooks/useEvents.js` | Fetches paginated events with current filter state. |
| `hooks/useStatistics.js` | Fetches stats with periodic auto-refresh. |
| `components/layout/Sidebar.jsx` | Navigation menu (links to all 9 sections). |
| `components/layout/TopNav.jsx` | Page title + WebSocket connection status indicator. |
| `components/layout/Layout.jsx` | Sidebar + TopNav + `<Outlet>` content area. |
| `components/ui/Badge.jsx` | Coloured severity/category badge. |
| `components/ui/Card.jsx` | Stat card with number, label, icon. |
| `components/ui/DataTable.jsx` | Sortable, paginated table component. |
| `components/ui/Spinner.jsx` | Loading spinner. |
| `components/ui/EmptyState.jsx` | "No data yet" placeholder. |
| `components/ui/ErrorState.jsx` | Error display with retry button. |
| `pages/Login.jsx` | API key entry form. On submit → stores key → redirects to dashboard. |
| `pages/Dashboard.jsx` | Overview with stat cards, timeline chart, category pie, recent events. |
| `pages/LiveMonitor.jsx` | Real-time event feed from WebSocket. Pause/resume. Filter by severity/category. |
| `pages/EventsExplorer.jsx` | Full event table with search, filters, pagination. Click → EventDetail. |
| `pages/EventDetail.jsx` | Full detail for one event: all fields, evidence, analyst annotation form. |
| `pages/SourceIntelligence.jsx` | List of observed IPs with stats. Click → SourceDetail. |
| `pages/SourceDetail.jsx` | Per-IP stats, category/severity distribution, event history. |
| `pages/ThreatAnalytics.jsx` | Charts: event trends, top endpoints, severity over time. |
| `pages/DetectionRules.jsx` | List of registered detectors with names, categories, hit counts. |
| `pages/SystemSettings.jsx` | Engine status, DB status, queue depth, WebSocket connections. |
| `utils/formatters.js` | `formatDate()`, `formatSeverity()`, `formatCategory()` display helpers. |
| `utils/severity.js` | Maps severity string to Tailwind colour classes. |
| `utils/constants.js` | Display names for categories and severities. |

---

## 11. File Reference Table

| File | Layer | Role |
|------|-------|------|
| `engine/core/config.py` | Engine | Central numeric configuration |
| `engine/core/context.py` | Engine | `RequestContext` frozen dataclass |
| `engine/core/detection.py` | Engine | `DetectionResult`, `Severity`, `AttackCategory` |
| `engine/core/engine.py` | Engine | Detector orchestrator |
| `engine/rules/signatures.py` | Engine | Compiled regexes + sensitive paths |
| `engine/collectors/request_collector.py` | Engine | Raw bytes → `RequestContext` |
| `engine/detectors/base.py` | Engine | Abstract detector base class |
| `engine/detectors/*.py` (8 files) | Engine | Individual attack detectors |
| `engine/analyzers/behavior.py` | Engine | Per-IP threat score |
| `engine/analyzers/automation.py` | Engine | Automation likelihood |
| `engine/analyzers/session_analyzer.py` | Engine | Session grouping |
| `engine/events/event.py` | Engine | `SecurityEvent` dataclass |
| `engine/events/storage_interface.py` | Engine | `EventSink` abstract class (**boundary**) |
| `engine/events/event_processor.py` | Engine | Merge results → `SecurityEvent` → `sink.save()` |
| `engine/network/ip_utils.py` | Engine | IP helpers |
| `engine/network/port_scan_detector.py` | Engine | Port scan detection |
| `engine/network/connection_monitor.py` | Engine | Decoy TCP port listeners |
| `engine/server/response_simulator.py` | Engine | Fake HTTP responses |
| `engine/server/request_handler.py` | Engine | Per-connection logic |
| `engine/server/http_server.py` | Engine | `asyncio.start_server` decoy listener |
| `backend/config.py` | Backend | Settings from `.env` |
| `backend/auth.py` | Backend | API key authentication |
| `backend/database/connection.py` | Backend | SQLAlchemy async engine + session |
| `backend/database/models.py` | Backend | ORM table definitions |
| `backend/database/repository.py` | Backend | All database queries |
| `backend/integration/event_sink.py` | Integration | `BackendEventSink` (implements `EventSink`) |
| `backend/integration/event_mapper.py` | Integration | Engine object → plain dict |
| `backend/integration/engine_adapter.py` | Integration | Queue + worker task |
| `backend/services/event_service.py` | Backend | Save + broadcast |
| `backend/services/ws_manager.py` | Backend | WebSocket connection manager |
| `backend/api/routes/health.py` | API | `GET /api/health` |
| `backend/api/routes/events.py` | API | Events CRUD |
| `backend/api/routes/attackers.py` | API | Source intelligence |
| `backend/api/routes/statistics.py` | API | Aggregated stats |
| `backend/api/routes/detectors.py` | API | Detector list |
| `backend/api/routes/system.py` | API | System status |
| `backend/api/websockets/events.py` | API | WebSocket endpoint |
| `backend/main.py` | Backend | FastAPI app + startup lifecycle |
| `frontend/src/services/api.js` | Frontend | Axios HTTP client |
| `frontend/src/services/websocket.js` | Frontend | WebSocket client |
| `frontend/src/hooks/useWebSocket.js` | Frontend | React WS state hook |
| `frontend/src/hooks/useAuth.js` | Frontend | API key management |
| `frontend/src/pages/*.jsx` (10 pages) | Frontend | Dashboard pages |
| `frontend/src/components/layout/*.jsx` | Frontend | App shell |
| `frontend/src/components/ui/*.jsx` | Frontend | Reusable UI elements |

---

## 12. Data Object Reference

### RequestContext (engine/core/context.py)
```
source_ip: str          validated IPv4/IPv6
source_port: int
method: str             GET, POST, etc.
path: str               URL-decoded
query_params: dict      URL-decoded
headers: dict           sensitive fields redacted
body: bytes             truncated to 8 KB
timestamp: datetime     UTC
request_id: str         UUID4
```

### DetectionResult (engine/core/detection.py)
```
detector_name: str      e.g. 'SQLInjectionDetector'
category: AttackCategory  enum
severity: Severity        enum: low | medium | high | critical
confidence: float         0.0 – 1.0
reason: str             human-readable explanation
evidence: dict          raw matched values (never executed)
```

### SecurityEvent (engine/events/event.py)
```
event_id: uuid.UUID
source_ip: str
timestamp: datetime
attack_category: AttackCategory
severity: Severity
confidence: float
detection_reasons: list[str]
evidence: dict
target: str
method: str
path: str
request_id: str
detector_names: list[str]
related_results: list[DetectionResult]
metadata: dict          {behavioral, automation, session scores}
```

### WebSocket Message (from backend to browser)
```json
{
  "type": "security_event",
  "data": {
    "event_id": "uuid-string",
    "source_ip": "1.2.3.4",
    "timestamp": "2026-11-25T10:00:00Z",
    "attack_category": "sql_injection",
    "severity": "high",
    "confidence": 0.85,
    "target": "/login",
    "method": "POST",
    "path": "/login",
    "detector_names": ["SQLInjectionDetector"],
    "detection_reasons": ["Suspicious SQL pattern: UNION SELECT"]
  }
}
```

---

## 13. Dependency Rules

```
engine/          ← NEVER imports from backend/ or frontend/
backend/         ← imports only engine/events/storage_interface.py (EventSink)
frontend/        ← calls backend/ via HTTP and WebSocket only
```

```
engine/rules/signatures.py  ← imported by all detectors
engine/core/config.py       ← imported by stateful detectors and collector
engine/detectors/base.py    ← inherited by all detector implementations
```

**Circular import prevention:**
- `backend/api/routes/statistics.py` imports `detection_engine` from `backend/main.py` lazily (inside the route function), not at module level.
- Same pattern used in `detectors.py` and `system.py` routes.

---

## 14. Port Reference

| Port | Service | Binds to | Purpose |
|------|---------|----------|---------|
| **8080** | Honeypot HTTP | `0.0.0.0` | Receives untrusted traffic — the decoy |
| **8000** | FastAPI management | `127.0.0.1` | REST API + WebSocket — management only |
| **5173** | Vite dev server | `localhost` | React frontend dev server |
| 21, 22, 23, ... | Decoy TCP | `0.0.0.0` | Port scan detection listeners |

> [!WARNING]
> During development, the management API (port 8000) must only bind to `127.0.0.1`. Never expose it to the public internet.

---

## 15. Startup Sequence

```
python -m uvicorn backend.main:app --port 8000
         │
         ▼  lifespan() starts
1. init_db()
   └── Creates data/database/honeypot.db if not present
   └── Runs CREATE TABLE IF NOT EXISTS for all 4 tables

2. engine_adapter.start(AsyncSessionLocal)
   └── Creates asyncio.Queue(maxsize=1000)
   └── Creates BackendEventSink(queue, dropped_counter)
   └── Starts _worker_loop() as asyncio.Task

3. Register detectors into DetectionEngine:
   SQLInjectionDetector, XSSDetector, PathTraversalDetector,
   CommandInjectionDetector, DirectoryEnumerationDetector,
   EndpointEnumerationDetector, BruteForceDetector,
   SuspiciousRequestDetector

4. Build pipeline:
   RequestCollector → RequestHandler → HoneypotHTTPServer

5. Start decoy HTTP listener on port 8080

6. FastAPI begins serving management API on port 8000
         │
         ▼  request arrives at port 8080
       [data flow from Section 2 begins]
```

---

## 16. How to Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and configure environment
cp .env.example .env
# Edit .env: set API_KEY to something secure

# 3. Start the backend (includes honeypot listener)
cd /home/hardik7219/FILES/php/HoneyPot
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 4. In another terminal, start the frontend
cd frontend
npm install
npm run dev

# 5. Open the dashboard
# http://localhost:5173
# Enter your API_KEY from .env

# 6. Test with the attack simulator
python scripts/simulate_attacks.py
```

---

*This document should be updated whenever a new detector, API route, or frontend page is added.*
