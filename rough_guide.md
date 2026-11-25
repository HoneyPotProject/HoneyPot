## features

```
port scanning
directory and enpoint enumeration 
sql injection 
cross-site scripting
suspicious http requests
Attempts to access administrative endpoints.
```
--- 
```
Which tools or clients they use
Brute-force patterns
What resources attackers target
What attackers try to execute
Whether an attack is automated
```
---
```
Source IP addresses.
Suspicious domains.
Malicious URLs.
Attack payload signatures.
```
---

## need knowledge
```
Networking fundamentals	IP, TCP, UDP, ports, DNS
HTTP/HTTPS	Methods, headers, status codes, requests
OSI model	How network communication works
TCP/IP	How devices communicate
Port scanning	How attackers discover services
Reconnaissance	How attackers gather information
Brute-force attacks	Repeated login attempts
SQL injection	Malicious database queries
XSS	Malicious browser-side scripts
Path traversal	Attempts to access restricted files
Command injection	Attempts to execute system commands
Authentication	Login and credential handling
Threat intelligence	IPs, domains, URLs, hashes
Log analysis	Understanding security events
```
---
## skill and technologies
```
Technology-	Purpose	Priority
FastAPI-	Backend API	Essential
Uvicorn-	ASGI server	Essential
asyncio-	Asynchronous processing	Essential
socket-	Network programming	Important
Pydantic-	Data validation	Essential
SQLAlchemy-	Database ORM	Recommended
hashlib-	SHA-256 file hashing	Important
re-	Pattern matching	Essential
ipaddress-	IP address validation	Important
logging-	Event and application logging	Essential
pytest-	Automated testing	Essential
```



## What each file does
```
engine/core/
File	Purpose
context.py	Defines RequestContext, a frozen dataclass with source IP, method, path, query params, headers, size-limited body, timestamp and request ID. Every detector receives only this object.
detection.py	Defines DetectionResult (detector name, category, severity, confidence, reason, evidence) plus Severity and AttackCategory enums.
engine.py	DetectionEngine. Registers detectors, runs them on each RequestContext, wraps each in try/except so one crash never stops the others, and returns the list of results.
config.py	Engine settings: body size limit, time windows, thresholds, redaction list. Using one place means you won't scatter magic numbers through the detectors.
engine/collectors/
File	Purpose
request_collector.py	Turns raw HTTP data into a RequestContext. It validates the IP with ipaddress, parses the URL and query string, URL-decodes values, truncates the body to the size limit, and redacts Authorization, Cookie and password fields.
engine/detectors/
File	Purpose
base.py	Abstract BaseDetector with name, category and analyze(ctx) -> list[DetectionResult]. All detectors inherit it, so adding a new one means adding a file and registering it.
directory_enum.py	Flags requests to sensitive paths such as /.env, /.git/config, /wp-admin, /phpmyadmin and /backup.zip. Stateless.
endpoint_enum.py	Flags one IP requesting many distinct paths, or many 404s, in a time window. Stateful, using a per-IP deque with a size cap.
sql_injection.py	Decodes input repeatedly, then matches SQL patterns (UNION SELECT, OR 1=1, comments, stacked queries). Reports "suspicious pattern", never "successful injection".
xss.py	Matches <script>, event-handler attributes, javascript: URLs and encoded variants.
path_traversal.py	Finds ../, ..\, and single, double and unicode-encoded forms. Normalizes paths before matching.
command_injection.py	Finds shell separators (;, &&, |, backticks, $()) combined with command-like words. Never executes anything.
brute_force.py	Counts login attempts per IP in a sliding window against the fake login endpoint and flags when a threshold is crossed. Stateful.
suspicious_request.py	Flags malformed requests, missing or odd headers, oversized headers and unusual methods. Uses low confidence, since headers alone prove little.
engine/analyzers/
File	Purpose
behavior.py	Correlates events per source IP over time: repeated categories, multiple attack types, sequential scanning. Produces a behavioral score.
automation.py	Estimates automation likelihood from request timing, rate, and regularity. User-Agent is a weak hint only.
session_analyzer.py	Groups requests into sessions (IP plus time gap, and cookie if present) and tracks per-session activity.
engine/events/
File	Purpose
event.py	Defines SecurityEvent: event ID, IP, timestamp, category, severity, confidence, reasons, evidence, target, method, path, related results.
event_processor.py	Merges detector results and analyzer output into one normalized SecurityEvent, generates the UUID, picks the final category and severity, and passes the event to the sink. This is the only place where classification happens.
storage_interface.py	An abstract EventSink with save(event). The backend provides the SQLite implementation and tests provide an in-memory one.
engine/network/
File	Purpose
connection_monitor.py	asyncio listeners on several decoy TCP ports. It logs each connection (IP, port, time) without serving real content.
port_scan_detector.py	Flags one IP hitting many different decoy ports within a window.
ip_utils.py	IP validation, private/public classification and normalization helpers.
engine/rules/
File	Purpose
signatures.py	All compiled regexes and path lists, grouped by category. Detectors import from here, so you can tune rules without touching detector logic.
engine/server/
File	Purpose
http_server.py	The decoy HTTP listener, built on asyncio.start_server, with request size limits and timeouts.
request_handler.py	Parses the raw request, calls the collector, runs the engine, passes results to the processor, then asks the simulator for a response.
response_simulator.py	Returns fake responses: a fake login page, fake 403/404, and a fake /admin. It never reads host files or runs input.
backend/
File	Purpose
main.py	Creates the FastAPI app, registers routers and WebSocket, sets CORS, and starts the engine and honeypot as background tasks.
config.py	Loads settings from .env using pydantic-settings: ports, DB path, API key.
auth.py	API key or token check for management endpoints.
api/dependencies.py	Shared dependencies: DB session and auth.
api/routes/health.py	GET /api/health
api/routes/events.py	GET /api/events (filters, pagination) and GET /api/events/{id}
api/routes/statistics.py	GET /api/statistics: totals, categories, severity counts, time series, top paths.
api/routes/attackers.py	GET /api/attackers and /api/attackers/{ip}
api/routes/detectors.py	GET /api/detectors: lists registered detectors and whether each is enabled.
api/websockets/events.py	/ws/events endpoint that streams new events to connected clients.
database/connection.py	SQLAlchemy engine and session factory.
database/models.py	ORM tables: security_events, detection_results, source_observations, optional sessions.
database/repository.py	All queries (create, filter, paginate, aggregate), and the EventSink implementation.
schemas/*.py	Pydantic request and response models.
services/event_service.py	Glue: runs the repository save, then broadcasts through the WebSocket manager.
services/ws_manager.py	Tracks connected clients and broadcasts safely, removing dead connections.
```