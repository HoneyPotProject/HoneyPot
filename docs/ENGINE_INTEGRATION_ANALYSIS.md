# ENGINE INTEGRATION ANALYSIS

**Produced:** 2026-11-25  
**Purpose:** Document the existing repository state before any implementation begins, identify all integration requirements, and define the precise plan for connecting the detection engine to the FastAPI backend.

---

## 1. Repository Inspection Summary

### 1.1 Inspection Method

Every file in the repository was opened and read. No class, interface, or import path in this document is invented.

### 1.2 Critical Finding — Stub-Only Repository

**Every engine file currently contains exactly one line: a comment describing what the file is supposed to do.**

No Python class, function, import statement, enum, or dataclass exists yet in any engine file. The repository is a **design-only scaffold**. The comments are authoritative design specifications, not documentation of working code.

This means:

- There is no working `RequestContext` dataclass.
- There is no working `DetectionResult` dataclass.
- There is no working `DetectionEngine` class.
- There is no working `SecurityEvent` dataclass.
- There is no working `EventProcessor` class.
- There is no working `EventSink` abstract class.
- There is no working HTTP listener.
- There is no working detector of any kind.
- There is no working backend.
- There is no working database.

The backend files (`main.py`, `config.py`, `auth.py`, all route files, all schema files, all service files, all database files) are completely empty (0 bytes).

The `requirements.txt`, `.env.example`, `pyproject.toml` and all `docs/*.md` files are also empty or contain only a comment.

The `tests/` directory exists with subdirectories (`unit/`, `integration/`, `security/`) and a `conftest.py`, but all are empty.

---

## 2. Existing File Structure (Actual)

```
HoneyPot/
├── .env.example                    EMPTY
├── .gitignore                      present
├── README.md                       present (not inspected — not in engine)
├── alembic/                        EMPTY directory
├── backend/
│   ├── api/
│   │   ├── dependencies.py         EMPTY
│   │   ├── routes/
│   │   │   ├── attackers.py        EMPTY
│   │   │   ├── detectors.py        EMPTY
│   │   │   ├── events.py           EMPTY
│   │   │   ├── health.py           EMPTY
│   │   │   └── statistics.py       EMPTY
│   │   └── websockets/
│   │       └── events.py           EMPTY
│   ├── auth.py                     EMPTY
│   ├── config.py                   EMPTY
│   ├── database/
│   │   ├── connection.py           EMPTY
│   │   ├── models.py               EMPTY
│   │   └── repository.py           EMPTY
│   ├── main.py                     EMPTY
│   ├── schemas/
│   │   ├── attacker.py             EMPTY
│   │   ├── event.py                EMPTY
│   │   └── statistics.py           EMPTY
│   └── services/
│       ├── event_service.py        EMPTY
│       └── ws_manager.py           EMPTY
├── data/
│   ├── database/                   EMPTY directory
│   └── logs/                       EMPTY directory
├── docs/
│   ├── api-documentation.md        EMPTY
│   ├── architecture.md             EMPTY
│   ├── detection-rules.md          EMPTY
│   ├── rough_guide.md              127-line design guide (readable)
│   └── security-isolation.md       EMPTY
├── engine/
│   ├── analyzers/
│   │   ├── automation.py           STUB COMMENT ONLY
│   │   ├── behavior.py             STUB COMMENT ONLY
│   │   └── session_analyzer.py     STUB COMMENT ONLY
│   ├── collectors/
│   │   └── request_collector.py    STUB COMMENT ONLY
│   ├── core/
│   │   ├── config.py               STUB COMMENT ONLY
│   │   ├── context.py              STUB COMMENT ONLY
│   │   ├── detection.py            STUB COMMENT ONLY
│   │   └── engine.py               STUB COMMENT ONLY
│   ├── detectors/
│   │   ├── base.py                 STUB COMMENT ONLY
│   │   ├── brute_force.py          STUB COMMENT ONLY
│   │   ├── command_injection.py    STUB COMMENT ONLY
│   │   ├── directory_enum.py       STUB COMMENT ONLY
│   │   ├── endpoint_enum.py        STUB COMMENT ONLY
│   │   ├── path_traversal.py       STUB COMMENT ONLY
│   │   ├── sql_injection.py        STUB COMMENT ONLY
│   │   ├── suspicious_request.py   STUB COMMENT ONLY
│   │   └── xss.py                  STUB COMMENT ONLY
│   ├── events/
│   │   ├── event.py                STUB COMMENT ONLY
│   │   ├── event_processor.py      STUB COMMENT ONLY
│   │   └── storage_interface.py    STUB COMMENT ONLY
│   ├── network/
│   │   ├── connection_monitor.py   STUB COMMENT ONLY
│   │   ├── ip_utils.py             STUB COMMENT ONLY
│   │   └── port_scan_detector.py   STUB COMMENT ONLY
│   ├── rules/
│   │   └── signatures.py           STUB COMMENT ONLY
│   └── server/
│       ├── http_server.py          STUB COMMENT ONLY
│       ├── request_handler.py      STUB COMMENT ONLY
│       └── response_simulator.py   STUB COMMENT ONLY
├── frontend/
│   ├── package.json                React 19.3 + Vite 8.3 (no TypeScript, no Tailwind)
│   ├── src/
│   │   ├── App.jsx                 Default Vite welcome screen (not a dashboard)
│   │   ├── main.jsx                Standard React entry point
│   │   ├── index.css               Vite default styles
│   │   ├── App.css                 Vite default styles
│   │   ├── components/             EMPTY directory
│   │   ├── hooks/                  EMPTY directory
│   │   ├── pages/                  EMPTY directory
│   │   ├── services/               EMPTY directory
│   │   ├── types/                  EMPTY directory
│   │   └── utils/                  EMPTY directory
│   └── vite.config.js              Minimal Vite config (React plugin only)
├── pyproject.toml                  STUB COMMENT ONLY
├── requirements.txt                EMPTY
├── scripts/
│   ├── run_all.py                  STUB COMMENT ONLY
│   └── simulate_attacks.py         STUB COMMENT ONLY
└── tests/
    ├── conftest.py                 EMPTY
    ├── integration/                EMPTY directory
    ├── security/                   EMPTY directory
    └── unit/                       EMPTY directory
```

---

## 3. Design Specifications Extracted from Stubs

The single-line comments in each file are authoritative specifications from the developer. They define exactly what each module must implement.

### 3.1 Engine Core

| File | Specified behaviour |
|------|-------------------|
| `engine/core/context.py` | Frozen dataclass `RequestContext`: source IP, method, path, query params, headers, size-limited body, timestamp, request ID. This is the only object detectors receive. |
| `engine/core/detection.py` | `DetectionResult` dataclass: detector name, category, severity, confidence, reason, evidence. Enums: `Severity`, `AttackCategory`. |
| `engine/core/engine.py` | `DetectionEngine`: registers detectors, runs all of them on each `RequestContext`, wraps each in `try/except` so one crash never stops others, returns list of `DetectionResult`. |
| `engine/core/config.py` | `EngineConfig`: body size limit, time windows, thresholds, redaction list. Single location for all magic numbers. |

### 3.2 Engine Collectors

| File | Specified behaviour |
|------|-------------------|
| `engine/collectors/request_collector.py` | `RequestCollector`: validates IP with `ipaddress`, parses URL and query string, URL-decodes values, truncates body to limit, redacts `Authorization`, `Cookie`, `password` fields. Returns `RequestContext`. |

### 3.3 Engine Detectors

| File | Specified behaviour |
|------|-------------------|
| `engine/detectors/base.py` | `BaseDetector`: abstract class with `name`, `category`, `analyze(ctx) -> list[DetectionResult]`. |
| `engine/detectors/directory_enum.py` | Stateless. Flags requests to `/.env`, `/.git/config`, `/wp-admin`, `/phpmyadmin`, `/backup.zip`, etc. |
| `engine/detectors/endpoint_enum.py` | Stateful (per-IP deque with size cap). Flags one IP requesting many distinct paths or many 404s in a time window. |
| `engine/detectors/sql_injection.py` | Stateless. Decodes input repeatedly, matches `UNION SELECT`, `OR 1=1`, comments, stacked queries. Never reports "successful injection", only "suspicious pattern". |
| `engine/detectors/xss.py` | Stateless. Matches `<script>`, event-handler attributes, `javascript:` URLs, encoded variants. |
| `engine/detectors/path_traversal.py` | Stateless. Finds `../`, `..\`, single/double/unicode-encoded forms, normalizes paths before matching. |
| `engine/detectors/command_injection.py` | Stateless. Finds shell separators (`;`, `&&`, `\|`, backticks, `$()`) combined with command-like words. Never executes anything. |
| `engine/detectors/brute_force.py` | Stateful. Counts login attempts per IP in a sliding window against the fake login endpoint, flags when threshold crossed. |
| `engine/detectors/suspicious_request.py` | Stateless (low confidence). Flags malformed requests, missing/odd headers, oversized headers, unusual methods. |

### 3.4 Engine Analyzers

| File | Specified behaviour |
|------|-------------------|
| `engine/analyzers/behavior.py` | Correlates events per source IP over time: repeated categories, multiple attack types, sequential scanning. Produces a behavioural score. |
| `engine/analyzers/automation.py` | Estimates automation likelihood from request timing, rate, and regularity. User-Agent is a weak hint only. |
| `engine/analyzers/session_analyzer.py` | Groups requests into sessions (IP + time gap + cookie if present), tracks per-session activity. |

### 3.5 Engine Events

| File | Specified behaviour |
|------|-------------------|
| `engine/events/event.py` | `SecurityEvent`: event ID, IP, timestamp, category, severity, confidence, reasons, evidence, target, method, path, related results. |
| `engine/events/event_processor.py` | `EventProcessor`: merges detector results + analyzer output into one normalized `SecurityEvent`. Generates UUID, picks final category and severity. Passes event to sink. **This is the only place classification happens.** |
| `engine/events/storage_interface.py` | Abstract `EventSink` with `save(event)`. Backend provides SQLite implementation; tests provide in-memory implementation. |

### 3.6 Engine Network

| File | Specified behaviour |
|------|-------------------|
| `engine/network/connection_monitor.py` | `asyncio` listeners on several decoy TCP ports. Logs each connection (IP, port, time) without serving real content. |
| `engine/network/ip_utils.py` | IP validation, private/public classification, normalization helpers. |
| `engine/network/port_scan_detector.py` | Flags one IP hitting many different decoy ports within a window. |

### 3.7 Engine Rules

| File | Specified behaviour |
|------|-------------------|
| `engine/rules/signatures.py` | All compiled regexes and path lists, grouped by category. Detectors import from here. Tuning rules does not require touching detector logic. |

### 3.8 Engine Server

| File | Specified behaviour |
|------|-------------------|
| `engine/server/http_server.py` | Decoy HTTP listener built on `asyncio.start_server`. Applies request size limits and timeouts. |
| `engine/server/request_handler.py` | Parses raw request → calls collector → runs engine → passes results to processor → asks simulator for response. |
| `engine/server/response_simulator.py` | Returns fake responses: fake login page, fake 403/404, fake `/admin`. Never reads host files or runs input. |

### 3.9 Backend (from `rough_guide.md`)

| File | Specified behaviour |
|------|-------------------|
| `backend/main.py` | Creates FastAPI app, registers routers and WebSocket, sets CORS, starts engine and honeypot as background tasks. |
| `backend/config.py` | Loads settings from `.env` using `pydantic-settings`: ports, DB path, API key. |
| `backend/auth.py` | API key or token check for management endpoints. |
| `backend/api/dependencies.py` | Shared dependencies: DB session and auth. |
| `backend/api/routes/health.py` | `GET /api/health` |
| `backend/api/routes/events.py` | `GET /api/events` (filters, pagination) and `GET /api/events/{id}` |
| `backend/api/routes/statistics.py` | `GET /api/statistics` |
| `backend/api/routes/attackers.py` | `GET /api/attackers` and `GET /api/attackers/{ip}` |
| `backend/api/routes/detectors.py` | `GET /api/detectors` |
| `backend/api/websockets/events.py` | `/ws/events` endpoint, streams new events. |
| `backend/database/connection.py` | SQLAlchemy engine and session factory. |
| `backend/database/models.py` | ORM tables: `security_events`, `detection_results`, `source_observations`, optional sessions. |
| `backend/database/repository.py` | All queries (create, filter, paginate, aggregate), plus the `EventSink` implementation. |
| `backend/schemas/*.py` | Pydantic request and response models. |
| `backend/services/event_service.py` | Runs repository save, then broadcasts through WebSocket manager. |
| `backend/services/ws_manager.py` | Tracks connected clients, broadcasts safely, removes dead connections. |

---

## 4. Event Processing Flow (Designed, Not Yet Implemented)

The design specification describes the following flow:

```
Raw HTTP bytes arrive at decoy port
        │
        ▼
engine/server/http_server.py
  asyncio.start_server listener
        │
        ▼
engine/server/request_handler.py
  Parse raw HTTP → call RequestCollector
        │
        ▼
engine/collectors/request_collector.py
  Validate IP, parse URL, URL-decode, redact secrets, truncate body
  → produce RequestContext (frozen dataclass)
        │
        ▼
engine/core/engine.py  (DetectionEngine)
  For each registered BaseDetector:
    try: detector.analyze(ctx) → list[DetectionResult]
    except: log, continue
  Returns all DetectionResult objects
        │
        ▼
engine/analyzers/behavior.py
engine/analyzers/automation.py
engine/analyzers/session_analyzer.py
  Produce behavioural scores / automation estimates / session data
        │
        ▼
engine/events/event_processor.py  (EventProcessor)
  Merge results + analyzer output
  Generate UUID event_id
  Pick final category (highest-severity or most-confident detector wins)
  Pick final severity
  Build SecurityEvent
        │
        ▼
engine/events/storage_interface.py  (EventSink.save(event))
  Abstract method — backend provides concrete implementation
        │
        ▼
backend/database/repository.py  (BackendEventSink)
  Write to SQLite via SQLAlchemy
  → Upsert SourceObservation
        │
        ├──► backend/services/event_service.py
        │      Notify WebSocket manager
        │
        └──► backend/api/websockets/events.py
               Broadcast JSON to all connected React clients
```

---

## 5. Missing Components — Complete List

Since the entire project is stubs, **every implementation component is missing**. The following list prioritises by dependency order.

### Priority 1 — Engine Core (must exist before anything can run)

- [ ] `engine/__init__.py` — package marker
- [ ] `engine/core/__init__.py` — package marker
- [ ] `engine/core/config.py` — `EngineConfig` dataclass
- [ ] `engine/core/context.py` — `RequestContext` frozen dataclass
- [ ] `engine/core/detection.py` — `DetectionResult`, `Severity` enum, `AttackCategory` enum
- [ ] `engine/core/engine.py` — `DetectionEngine` class

### Priority 2 — Engine Rules and Collectors

- [ ] `engine/rules/__init__.py`
- [ ] `engine/rules/signatures.py` — compiled regex patterns, sensitive path lists
- [ ] `engine/collectors/__init__.py`
- [ ] `engine/collectors/request_collector.py` — `RequestCollector` class

### Priority 3 — Engine Detectors

- [ ] `engine/detectors/__init__.py`
- [ ] `engine/detectors/base.py` — `BaseDetector` abstract class
- [ ] `engine/detectors/directory_enum.py`
- [ ] `engine/detectors/endpoint_enum.py` (stateful)
- [ ] `engine/detectors/sql_injection.py`
- [ ] `engine/detectors/xss.py`
- [ ] `engine/detectors/path_traversal.py`
- [ ] `engine/detectors/command_injection.py`
- [ ] `engine/detectors/brute_force.py` (stateful)
- [ ] `engine/detectors/suspicious_request.py`

### Priority 4 — Engine Analyzers

- [ ] `engine/analyzers/__init__.py`
- [ ] `engine/analyzers/behavior.py`
- [ ] `engine/analyzers/automation.py`
- [ ] `engine/analyzers/session_analyzer.py`

### Priority 5 — Engine Events (Integration Boundary)

- [ ] `engine/events/__init__.py`
- [ ] `engine/events/event.py` — `SecurityEvent` dataclass
- [ ] `engine/events/storage_interface.py` — `EventSink` abstract class
- [ ] `engine/events/event_processor.py` — `EventProcessor` class

### Priority 6 — Engine Network

- [ ] `engine/network/__init__.py`
- [ ] `engine/network/ip_utils.py`
- [ ] `engine/network/connection_monitor.py`
- [ ] `engine/network/port_scan_detector.py`

### Priority 7 — Engine Server

- [ ] `engine/server/__init__.py`
- [ ] `engine/server/response_simulator.py`
- [ ] `engine/server/request_handler.py`
- [ ] `engine/server/http_server.py`

### Priority 8 — Backend Foundation

- [ ] `backend/__init__.py`
- [ ] `requirements.txt` — all Python dependencies
- [ ] `pyproject.toml` — proper project metadata
- [ ] `.env.example` — environment variable template
- [ ] `backend/config.py` — `Settings` via `pydantic-settings`
- [ ] `backend/database/connection.py` — SQLAlchemy async engine
- [ ] `backend/database/models.py` — ORM table definitions
- [ ] `backend/database/repository.py` — queries + `BackendEventSink`
- [ ] `alembic/` — migration configuration and initial migration

### Priority 9 — Backend Integration Layer

- [ ] `backend/integration/` — new directory (not in current structure)
- [ ] `backend/integration/__init__.py`
- [ ] `backend/integration/event_sink.py` — `BackendEventSink(EventSink)` adapter
- [ ] `backend/integration/event_mapper.py` — engine `SecurityEvent` → backend DB model
- [ ] `backend/integration/engine_adapter.py` — bounded `asyncio.Queue` + worker task

### Priority 10 — Backend Services and API

- [ ] `backend/services/ws_manager.py`
- [ ] `backend/services/event_service.py`
- [ ] `backend/schemas/event.py`
- [ ] `backend/schemas/attacker.py`
- [ ] `backend/schemas/statistics.py`
- [ ] `backend/schemas/detector.py` (not in current structure — needed)
- [ ] `backend/schemas/system.py` (not in current structure — needed)
- [ ] `backend/auth.py`
- [ ] `backend/api/dependencies.py`
- [ ] `backend/api/routes/health.py`
- [ ] `backend/api/routes/events.py`
- [ ] `backend/api/routes/attackers.py`
- [ ] `backend/api/routes/statistics.py`
- [ ] `backend/api/routes/detectors.py`
- [ ] `backend/api/routes/system.py` (not in current structure — needed)
- [ ] `backend/api/websockets/events.py`
- [ ] `backend/main.py`

### Priority 11 — Frontend

- [ ] TypeScript configuration (`tsconfig.json`)
- [ ] Update `package.json` to add: `typescript`, `@types/react`, `@types/react-dom`, `tailwindcss`, `axios`, `react-router-dom`, `recharts`, `lucide-react`
- [ ] All feature directories and components (complete rewrite of `src/`)

### Priority 12 — Supporting Files

- [ ] `scripts/run_all.py`
- [ ] `scripts/simulate_attacks.py`
- [ ] `tests/conftest.py`
- [ ] All unit, integration, and security tests

---

## 6. Integration Architecture — Chosen Design

### 6.1 Single-Process Development Architecture

For the initial development version, the engine and backend run in the **same Python process**, sharing an in-memory bounded queue. This is the simplest path to a working end-to-end system.

```
                   same Python process
    ┌─────────────────────────────────────────────────────────┐
    │                                                         │
    │  asyncio.start_server (decoy HTTP, port 8080)           │
    │       │                                                 │
    │       ▼                                                 │
    │  RequestHandler                                         │
    │       │  RequestCollector                               │
    │       │  DetectionEngine                                │
    │       │  Analyzers                                      │
    │       │  EventProcessor                                 │
    │       │       │                                         │
    │       │       ▼                                         │
    │       │  BackendEventSink (implements EventSink)        │
    │       │       │  asyncio.Queue(maxsize=1000)            │
    │       │       │                                         │
    │       │       ▼                                         │
    │  EventWorker (asyncio.Task)                             │
    │       │  EventService                                   │
    │       │  Repository → SQLite                            │
    │       │  WsManager → broadcast                          │
    │       │                                                 │
    │  Uvicorn ASGI (management API, port 8000)               │
    │       │  FastAPI REST endpoints                         │
    │       │  WebSocket /ws/events                           │
    │                                                         │
    └─────────────────────────────────────────────────────────┘
```

**In-memory queue limitation:** Events in the queue at the time of a process crash are lost. This is acceptable for the initial development version and must be documented. A durable queue (Redis Streams, SQLite WAL, etc.) can be introduced later.

### 6.2 Multi-Process Architecture (Future)

If the honeypot must run as a separate process (e.g., for privilege separation):

```
Process 1: Honeypot Engine
  → emits events to a restricted local HTTP endpoint: POST http://127.0.0.1:8000/internal/events
  → endpoint protected by a shared secret not visible to external traffic

Process 2: FastAPI Backend
  → receives events at /internal/events (loopback only)
  → enqueues into bounded asyncio.Queue
  → continues as before
```

The backend binds the internal endpoint to `127.0.0.1` only. The decoy listener binds to a separate interface or port. These are never on the same socket.

### 6.3 Dependency Direction Rule

```
engine/events/storage_interface.py defines EventSink (abstract)
           ▲
           │  inherits
           │
backend/integration/event_sink.py defines BackendEventSink

The engine NEVER imports from backend/.
The backend imports EventSink from engine/events/storage_interface.py.
```

This is the only cross-module import that is acceptable. All other engine modules remain completely independent of the backend.

---

## 7. `EventSink` Interface Design

Based on the stub comment in `engine/events/storage_interface.py`:

> "An abstract EventSink with save(event). The backend provides the SQLite implementation and tests provide an in-memory one."

The interface will be:

```python
# engine/events/storage_interface.py

import abc
from engine.events.event import SecurityEvent


class EventSink(abc.ABC):
    """
    Abstract storage interface for security events.

    The engine knows only this interface.
    The backend provides a concrete implementation.
    Tests provide an in-memory implementation.
    """

    @abc.abstractmethod
    async def save(self, event: SecurityEvent) -> None:
        """
        Persist or forward a security event.

        Must not raise exceptions that would propagate to the detection engine.
        Must handle failures internally (log and continue).
        """
        raise NotImplementedError
```

The `BackendEventSink` in `backend/integration/event_sink.py` will implement this:

```python
# backend/integration/event_sink.py

import asyncio
import logging
from engine.events.storage_interface import EventSink
from engine.events.event import SecurityEvent

logger = logging.getLogger(__name__)

class BackendEventSink(EventSink):
    def __init__(self, queue: asyncio.Queue, dropped_counter: list[int]):
        self._queue = queue
        self._dropped = dropped_counter  # mutable container for metrics

    async def save(self, event: SecurityEvent) -> None:
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            self._dropped[0] += 1
            logger.warning(
                "Event queue full — event dropped",
                extra={"event_id": str(event.event_id), "source_ip": event.source_ip}
            )
        except Exception as exc:
            logger.error("Unexpected error enqueuing event: %s", exc)
```

---

## 8. `SecurityEvent` Design

Based on `engine/events/event.py` stub:

> "Defines SecurityEvent: event ID, IP, timestamp, category, severity, confidence, reasons, evidence, target, method, path, related results."

```python
# engine/events/event.py

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from engine.core.detection import AttackCategory, Severity, DetectionResult


@dataclass
class SecurityEvent:
    event_id: uuid.UUID
    source_ip: str
    timestamp: datetime
    attack_category: AttackCategory
    severity: Severity
    confidence: float               # 0.0 – 1.0
    detection_reasons: list[str]
    evidence: dict[str, Any]
    target: str                     # e.g. "/wp-admin" or "port 22"
    method: str                     # HTTP method or "TCP" for port events
    path: str
    request_id: str
    detector_names: list[str]
    related_results: list[DetectionResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
```

---

## 9. `RequestContext` Design

Based on `engine/core/context.py` stub:

```python
# engine/core/context.py

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RequestContext:
    source_ip: str
    method: str
    path: str
    query_params: dict[str, str]
    headers: dict[str, str]        # Authorization, Cookie already redacted
    body: bytes                    # Truncated to body size limit
    timestamp: datetime
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
```

---

## 10. Import Paths (All Verified Against Actual File Locations)

| Import path | Physical location | Status |
|-------------|------------------|--------|
| `engine.core.context.RequestContext` | `engine/core/context.py` | To be implemented |
| `engine.core.detection.DetectionResult` | `engine/core/detection.py` | To be implemented |
| `engine.core.detection.Severity` | `engine/core/detection.py` | To be implemented |
| `engine.core.detection.AttackCategory` | `engine/core/detection.py` | To be implemented |
| `engine.core.engine.DetectionEngine` | `engine/core/engine.py` | To be implemented |
| `engine.core.config.EngineConfig` | `engine/core/config.py` | To be implemented |
| `engine.collectors.request_collector.RequestCollector` | `engine/collectors/request_collector.py` | To be implemented |
| `engine.detectors.base.BaseDetector` | `engine/detectors/base.py` | To be implemented |
| `engine.events.event.SecurityEvent` | `engine/events/event.py` | To be implemented |
| `engine.events.storage_interface.EventSink` | `engine/events/storage_interface.py` | To be implemented |
| `engine.events.event_processor.EventProcessor` | `engine/events/event_processor.py` | To be implemented |
| `engine.rules.signatures` | `engine/rules/signatures.py` | To be implemented |

---

## 11. Frontend Assessment

The frontend is a **default Vite + React scaffold**:

- `App.jsx` — Default Vite welcome screen with counter button. Not a dashboard.
- `package.json` — React 19.3 + Vite 8.3 only. No TypeScript, no Tailwind CSS, no routing, no HTTP client, no charting library, no icons.
- `src/components/` — Empty
- `src/pages/` — Empty
- `src/services/` — Empty
- `src/hooks/` — Empty
- `src/types/` — Empty
- `src/utils/` — Empty

The entire frontend application needs to be built. The existing `App.jsx` and default styles will be replaced. The Vite and React configuration (`vite.config.js`, `main.jsx`) will be updated.

**Important note on TypeScript:** The user's prompt specifies TypeScript, but the existing `package.json` uses `.jsx` and has no TypeScript configuration. The existing files are `.jsx`. The implementation will add TypeScript support and migrate to `.tsx`/`.ts` files, as this is what was specified.

---

## 12. Required `__init__.py` Files

The engine directory has no Python package marker files (`__init__.py`). These must be added to every engine subdirectory before any imports will work:

- `engine/__init__.py`
- `engine/core/__init__.py`
- `engine/collectors/__init__.py`
- `engine/detectors/__init__.py`
- `engine/analyzers/__init__.py`
- `engine/events/__init__.py`
- `engine/network/__init__.py`
- `engine/rules/__init__.py`
- `engine/server/__init__.py`
- `backend/__init__.py`
- `backend/api/__init__.py`
- `backend/api/routes/__init__.py`
- `backend/api/websockets/__init__.py`
- `backend/database/__init__.py`
- `backend/schemas/__init__.py`
- `backend/services/__init__.py`
- `backend/integration/__init__.py` (new directory)

---

## 13. Potential Architectural Conflicts

### 13.1 Single asyncio event loop

Both the decoy HTTP server (`asyncio.start_server`) and Uvicorn (which runs FastAPI) use `asyncio`. Running both in a single process requires starting the honeypot as an `asyncio.Task` inside the Uvicorn startup lifecycle, using `app.on_event("startup")` or a lifespan context manager.

**Risk:** If the honeypot or a detector blocks the event loop (e.g., with synchronous I/O), Uvicorn will stall. All honeypot I/O must be `async`.

**Mitigation:** Stateful detectors and analyzers use in-memory data structures only (no synchronous disk or network I/O). The request collector performs no I/O. All I/O goes through `asyncio`.

### 13.2 Stateful detectors and thread safety

The `brute_force.py` and `endpoint_enum.py` detectors are stateful. Their per-IP state (sliding windows, deques) must be safe for concurrent `asyncio` access. Since asyncio is cooperative (not preemptive), regular Python dicts and deques are safe as long as no `await` occurs in the middle of a state mutation.

**Rule:** State updates in detectors must be atomic at the Python level (no `await` between read and write of the same state).

### 13.3 Database blocking I/O

SQLAlchemy with SQLite can block the event loop if used with the synchronous driver. The implementation must use `aiosqlite` with SQLAlchemy's async extension (`create_async_engine`, `AsyncSession`).

**Alternative:** Use `run_in_executor` to run synchronous SQLAlchemy calls off the event loop. The async SQLAlchemy path is cleaner and is preferred.

### 13.4 Frontend language mismatch

The existing frontend uses `.jsx` (plain JavaScript). The implementation plan specifies TypeScript. Adding TypeScript requires:

1. Adding `typescript`, `@types/react`, `@types/react-dom` to `package.json`.
2. Adding `tsconfig.json`.
3. Updating `vite.config.js` to handle `.ts`/`.tsx`.
4. Renaming or replacing existing `.jsx` files with `.tsx`.

Since the existing `.jsx` files contain only the Vite default scaffold (no application logic), replacing them completely is appropriate.

---

## 14. Summary of Integration Requirements

| Requirement | Status | Notes |
|-------------|--------|-------|
| `EventSink` abstract class | Missing | Must implement in `engine/events/storage_interface.py` |
| `SecurityEvent` dataclass | Missing | Must implement in `engine/events/event.py` |
| `BackendEventSink` adapter | Missing | New file: `backend/integration/event_sink.py` |
| Bounded `asyncio.Queue` | Missing | Implemented in `backend/integration/engine_adapter.py` |
| Event worker task | Missing | Implemented in `backend/integration/engine_adapter.py` |
| `EventMapper` | Missing | New file: `backend/integration/event_mapper.py` |
| Engine `__init__.py` files | Missing | Required for Python package imports |
| All engine implementations | Missing | All files are stubs |
| All backend implementations | Missing | All files are empty |
| All frontend features | Missing | Only Vite default scaffold exists |
| `requirements.txt` | Empty | Must be populated |
| `.env.example` | Empty | Must be populated |
| `pyproject.toml` | Stub | Must be replaced with real TOML |
| Test suite | Empty | Must be built |

---

## 15. Files That Must NOT Be Deleted or Replaced

The following files contain the developer's authoritative design notes and must be preserved:

- `docs/rough_guide.md` — primary design reference
- All `engine/**/*.py` stub comments — they define the specification

The strategy is: **keep the comment, then add the implementation beneath it**.

---

*End of ENGINE_INTEGRATION_ANALYSIS.md*
