# HoneyPot — Phase-by-Phase Roadmap with Files & Code

> **Source:** `Honeypot_Build_Guide.pdf` Section 15, `master_prompt.md`, `CODE_FLOW.md`, `ENGINE_INTEGRATION_ANALYSIS.md`
>
> **Status:** Phase 1 ✅ Done | Phase 2 ✅ Done | Phase 3 → Current

---

## Phase 1 — Setup ✅ DONE

**Goal:** Folder tree, virtual environment, Git, tooling, README skeleton.
**Done when:** `pytest` and `ruff` run; frontend dev server opens.
**Difficulty:** Easy | **Time:** ~1 day

### Files created in this phase

| File | Location | Purpose |
|------|----------|---------|
| `.gitignore` | `HoneyPot/.gitignore` | Excludes `.venv/`, `.env`, `data/`, `__pycache__/`, `node_modules/`, `dist/` |
| `.env.example` | `HoneyPot/.env.example` | Environment variable template (no secrets) |
| `requirements.txt` | `HoneyPot/requirements.txt` | Python production dependencies |
| `requirements-dev.txt` | `HoneyPot/requirements-dev.txt` | Python dev dependencies (pytest, ruff) |
| `pyproject.toml` | `HoneyPot/pyproject.toml` | Project metadata, ruff config |
| `README.md` | `HoneyPot/README.md` | Project overview skeleton |
| `alembic.ini` | `HoneyPot/alembic.ini` | Alembic migration configuration |
| All `__init__.py` files | Every engine/ and backend/ subdirectory | Python package markers |
| `frontend/package.json` | `HoneyPot/frontend/package.json` | React + Vite project |
| `frontend/vite.config.js` | `HoneyPot/frontend/vite.config.js` | Vite config with API proxy |
| `tests/conftest.py` | `HoneyPot/tests/conftest.py` | Shared pytest fixtures |

---

## Phase 2 — Core Models ✅ DONE

**Goal:** `RequestContext`, `DetectionResult`, `SecurityEvent`, `BaseDetector`, `DetectionEngine`, config.
**Done when:** A dummy detector runs through the engine in a test.
**Difficulty:** Medium | **Time:** ~2-3 days

### Files created in this phase

---

#### `engine/core/config.py`
**Location:** `HoneyPot/engine/core/config.py`
**Purpose:** Central engine settings. All detectors read from here — no magic numbers scattered around.

```python
"""Central engine settings. Detectors read from here; they never hardcode limits."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EngineConfig:
    # Request limits (used later by the listener/collector)
    max_body_bytes: int = 16_384
    max_header_bytes: int = 8_192
    max_header_count: int = 64
    max_url_length: int = 2_048
    request_timeout_seconds: float = 10.0
    max_connections: int = 100

    # Normalizer
    max_decode_rounds: int = 3

    # Bounded memory for stateful detectors
    max_tracked_sources: int = 10_000
    max_entries_per_source: int = 200

    # Endpoint enumeration (starting values from the guide)
    endpoint_enum_distinct_paths: int = 15
    endpoint_enum_window_seconds: int = 60
    endpoint_enum_error_count: int = 10
    endpoint_enum_error_window_seconds: int = 30

    # Brute force
    brute_force_attempts: int = 5
    brute_force_window_seconds: int = 60

    # Port scan
    port_scan_distinct_ports: int = 5
    port_scan_window_seconds: int = 30

    # Sessions
    session_idle_gap_seconds: int = 1_800

    def __post_init__(self) -> None:
        for name, value in self.__dict__.items():
            if isinstance(value, (int, float)) and value <= 0:
                raise ValueError(f"{name} must be greater than 0")
```

---

#### `engine/core/context.py`
**Location:** `HoneyPot/engine/core/context.py`
**Purpose:** Frozen (immutable) dataclass that every detector receives. Contains source IP, method, path, query params, headers, body, timestamp, and request ID.

```python
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType


@dataclass(frozen=True)
class RequestContext:
    source_ip: str
    method: str
    path: str
    query_params: Mapping[str, str]
    headers: Mapping[str, str]
    body: str
    timestamp: datetime
    request_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "query_params", MappingProxyType(dict(self.query_params)))
        object.__setattr__(self, "headers", MappingProxyType(dict(self.headers)))
```

---

#### `engine/core/detection.py`
**Location:** `HoneyPot/engine/core/detection.py`
**Purpose:** Defines `DetectionResult` (what one detector returns), plus `Severity` and `AttackCategory` enums.

```python
"""Shared enums and the DetectionResult model."""

from dataclasses import dataclass
from enum import Enum


# severity enum
class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# attack enum
class AttackCategory(str, Enum):
    DIRECTORY_ENUMERATION = "directory_enumeration"
    ENDPOINT_ENUMERATION = "endpoint_enumeration"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    BRUTE_FORCE = "brute_force"
    SUSPICIOUS_REQUEST = "suspicious_request"
    PORT_SCAN = "port_scan"


@dataclass(frozen=True)  # like static class now can not be change
class DetectionResult:
    detector: str
    category: AttackCategory
    severity: Severity
    confidence: float
    reason: str
    evidence: str

    def __post_init__(self) -> None:
        if not isinstance(self.confidence, (int, float)) or isinstance(self.confidence, bool):
            raise TypeError("confidence must be a number")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
```

---

#### `engine/core/engine.py`
**Location:** `HoneyPot/engine/core/engine.py`
**Purpose:** Registers detectors, runs all of them on each `RequestContext`, wraps each in `try/except` so one crash never stops the others.

```python
import logging

from engine.core.context import RequestContext
from engine.core.detection import DetectionResult
from engine.detectors.base import BaseDetector

logger = logging.getLogger(__name__)


class DetectionEngine:
    def __init__(self) -> None:
        self._detectors: list[BaseDetector] = []

    @property
    def detectors(self) -> tuple[BaseDetector, ...]:
        return tuple(self._detectors)

    def register_detector(self, detector: BaseDetector) -> None:
        if not isinstance(detector, BaseDetector):
            raise TypeError("detector must inherit BaseDetector")
        if any(d.name == detector.name for d in self._detectors):
            raise ValueError(f"detector '{detector.name}' already registered")
        self._detectors.append(detector)

    def analyze(self, context: RequestContext) -> list[DetectionResult]:
        results: list[DetectionResult] = []
        for detector in self._detectors:
            if not detector.enabled:
                continue
            try:
                found = detector.analyze(context) or []
            except Exception:
                # Log the request ID only, never the raw payload.
                logger.exception(
                    "Detector '%s' failed on request %s",
                    detector.name,
                    context.request_id,
                )
                continue

            valid = [r for r in found if isinstance(r, DetectionResult)]
            if len(valid) != len(found):
                logger.warning("Detector '%s' returned invalid results", detector.name)
            detector.detection_count += len(valid)
            results.extend(valid)
        return results
```

---

#### `engine/detectors/base.py`
**Location:** `HoneyPot/engine/detectors/base.py`
**Purpose:** Abstract base class for all detectors. Every detector implements `name`, `category`, and `analyze()`.

```python
from abc import ABC, abstractmethod

from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult


class BaseDetector(ABC):
    description: str = ""
    version: str = "1.0"
    enabled: bool = True
    detection_count: int = 0

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique detector name, e.g. 'sql_injection'."""

    @property
    @abstractmethod
    def category(self) -> AttackCategory:
        """The attack category this detector reports."""

    @abstractmethod
    def analyze(self, context: RequestContext) -> list[DetectionResult]:
        """Return zero or more results. Must not modify context."""
```

---

#### `engine/events/event.py`
**Location:** `HoneyPot/engine/events/event.py`
**Purpose:** `SecurityEvent` — the consolidated event produced by the event processor after merging all detector results.

```python
"""SecurityEvent: the consolidated event produced by the event processor."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from engine.core.detection import AttackCategory, DetectionResult, Severity


@dataclass
class SecurityEvent:
    event_id: str
    source_ip: str
    timestamp: datetime
    attack_category: AttackCategory
    severity: Severity
    confidence: float
    detection_reasons: list[str]
    evidence: dict[str, Any]
    target: str
    method: str
    path: str
    request_id: str
    detector_names: list[str] = field(default_factory=list)
    related_results: list[DetectionResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
```

---

## Phase 3 — Collector + First Detector 🔄 CURRENT

**Goal:** Request collector, normalizer, directory enumeration detector, signatures file.
**Done when:** Sensitive paths detected; legitimate paths are not.
**Difficulty:** Medium | **Time:** ~2-3 days

### Files to create in this phase

---

#### `engine/core/normalizer.py` *(NEW FILE)*
**Location:** `HoneyPot/engine/core/normalizer.py`
**Purpose:** Input sanitization — decode URL encoding, remove null bytes, normalize Unicode, lowercase. Attackers encode payloads to evade simple string matching. This runs before any detector checks.

**What it does (plain English):**
- Takes a string (like a URL path or query value)
- URL-decodes it repeatedly up to `max_decode_rounds` (from config, default 3), stopping early if nothing changes
- Removes null bytes (`\x00`) — attackers insert these to confuse parsers
- Normalizes Unicode lookalike characters (e.g., fullwidth `Ａ` → normal `A`)
- Lowercases everything so `/.ENV` matches `/.env`

**Python concepts used:**
- `urllib.parse.unquote()` — URL decoding (like JavaScript's `decodeURIComponent`)
- `unicodedata.normalize("NFKC", text)` — Unicode normalization
- `.replace("\x00", "")` and `.lower()` — string methods

```python
"""Normalize untrusted input before detection.

Attackers encode payloads to evade simple string checks.
This module decodes, cleans, and normalizes text so detectors
can match patterns reliably.
"""

import unicodedata
from urllib.parse import unquote

from engine.core.config import EngineConfig

_DEFAULT_CONFIG = EngineConfig()


def normalize(text: str, config: EngineConfig = _DEFAULT_CONFIG) -> str:
    """Decode, clean and lowercase untrusted text.

    Steps:
      1. Bounded repeated URL-decoding (up to config.max_decode_rounds).
      2. Remove null bytes.
      3. Unicode NFKC normalization (lookalikes → standard form).
      4. Lowercase.
    """
    # Step 1 — bounded URL decode
    result = text
    for _ in range(config.max_decode_rounds):
        decoded = unquote(result)
        if decoded == result:      # nothing changed, stop early
            break
        result = decoded

    # Step 2 — remove null bytes
    result = result.replace("\x00", "")

    # Step 3 — Unicode normalization
    result = unicodedata.normalize("NFKC", result)

    # Step 4 — lowercase
    return result.lower()
```

---

#### `engine/rules/signatures.py`
**Location:** `HoneyPot/engine/rules/signatures.py`
**Purpose:** All compiled regexes and path lists, grouped by category. Detectors import from here, so you can tune rules without touching detector logic.

**What it does (plain English):**
- Contains curated lists of paths that attackers commonly scan for
- Split into "exact match" paths (like `/.env`) and "prefix match" paths (like `/.git/`)
- Also grouped by severity: secret-bearing paths are MEDIUM, admin/backup paths are LOW
- Later phases will add regex patterns for SQL injection, XSS, etc.

**Python concepts used:**
- `frozenset` — like a JavaScript `Set` but immutable, with O(1) lookup
- `tuple` — like a frozen array, used with `str.startswith()` for prefix checks

```python
"""Centralized signature rules for all detectors.

All compiled regexes and path lists live here, grouped by category.
Detectors import from here. Tune rules here, never in detector logic.

Phase 3: Directory enumeration paths.
Phase 4+: SQL injection, XSS, path traversal, command injection patterns.
"""

# ─── DIRECTORY ENUMERATION ─────────────────────────────────────────────

# Secret-bearing paths — higher severity (MEDIUM)
# These files often contain credentials, API keys, database passwords
SENSITIVE_EXACT_PATHS: frozenset[str] = frozenset({
    "/.env",
    "/.env.local",
    "/.env.production",
    "/.env.backup",
    "/.git/config",
    "/.git/HEAD",
    "/.gitignore",
    "/.aws/credentials",
    "/.ssh/id_rsa",
    "/.ssh/authorized_keys",
    "/.docker/config.json",
    "/wp-config.php",
    "/wp-config.php.bak",
    "/config.php",
    "/configuration.php",
    "/config.yml",
    "/config.yaml",
    "/config.json",
    "/.htaccess",
    "/.htpasswd",
    "/web.config",
    "/database.yml",
    "/settings.py",
    "/local_settings.py",
    "/.npmrc",
    "/.pypirc",
    "/id_rsa",
    "/id_dsa",
    "/.bash_history",
    "/.mysql_history",
    "/dump.sql",
    "/backup.sql",
    "/db.sql",
    "/database.sql",
    "/.DS_Store",
    "/thumbs.db",
    "/sftp-config.json",
    "/.svn/entries",
    "/.hg/hgrc",
})

# Secret-bearing prefix paths — files under these directories
SENSITIVE_PREFIX_PATHS: tuple[str, ...] = (
    "/.git/",
    "/.svn/",
    "/.hg/",
    "/.aws/",
    "/.ssh/",
    "/.docker/",
)

# Admin / tooling / backup paths — lower severity (LOW)
# These indicate scanning for admin panels or common tools
ADMIN_EXACT_PATHS: frozenset[str] = frozenset({
    "/admin",
    "/admin/",
    "/administrator",
    "/administrator/",
    "/phpmyadmin",
    "/phpmyadmin/",
    "/pma",
    "/pma/",
    "/adminer",
    "/adminer.php",
    "/wp-admin",
    "/wp-admin/",
    "/wp-login.php",
    "/wp-login",
    "/wp-content/",
    "/wp-includes/",
    "/joomla/administrator/",
    "/manager/",
    "/manager/html",
    "/console",
    "/console/",
    "/cpanel",
    "/cpanel/",
    "/webmail",
    "/webmail/",
    "/cgi-bin/",
    "/backup",
    "/backup/",
    "/backup.zip",
    "/backup.tar.gz",
    "/backup.tar",
    "/backup.rar",
    "/site.zip",
    "/site.tar.gz",
    "/www.zip",
    "/db.sql",
    "/debug",
    "/debug/",
    "/trace",
    "/trace/",
    "/actuator",
    "/actuator/",
    "/actuator/health",
    "/actuator/env",
    "/server-status",
    "/server-info",
    "/.well-known/",
    "/elmah.axd",
    "/info.php",
    "/phpinfo.php",
    "/test.php",
    "/info",
    "/robots.txt",
    "/sitemap.xml",
    "/crossdomain.xml",
    "/swagger-ui/",
    "/swagger-ui.html",
    "/api-docs",
    "/api-docs/",
    "/graphql",
    "/graphiql",
})

# Admin prefix paths
ADMIN_PREFIX_PATHS: tuple[str, ...] = (
    "/phpmyadmin/",
    "/wp-admin/",
    "/wp-content/",
    "/wp-includes/",
    "/cgi-bin/",
    "/actuator/",
    "/swagger-ui/",
    "/api-docs/",
)
```

---

#### `engine/collectors/request_collector.py`
**Location:** `HoneyPot/engine/collectors/request_collector.py`
**Purpose:** Turns raw HTTP request data into a `RequestContext` (the immutable object detectors receive). Validates IP, parses URL, truncates body, and redacts secrets.

**What it does (plain English):**
- Takes raw request data (IP, method, URL, headers, body)
- Validates the IP address is a real IP (not garbage text)
- Splits the URL into path and query parameters (like Express `req.path` and `req.query`)
- Truncates the body to `max_body_bytes` so attackers can't crash RAM
- Redacts sensitive headers (Authorization, Cookie, X-API-Key) → replaces values with `[REDACTED]`
- Redacts sensitive body fields (password, secret, token)
- Returns a frozen `RequestContext` with a UUID and UTC timestamp

**Python concepts used:**
- `ipaddress.ip_address()` — validates IP strings (raises `ValueError` if invalid)
- `urllib.parse.urlsplit` / `urllib.parse.parse_qs` — URL parsing (like `new URL()` in JS)
- `uuid.uuid4()` — generates a unique ID (like `crypto.randomUUID()` in JS)
- `datetime.now(timezone.utc)` — current UTC time

```python
"""Turn raw HTTP request data into an immutable RequestContext.

Validates the source IP, parses the URL, URL-decodes values,
truncates the body, and redacts sensitive headers and fields.
"""

import ipaddress
import logging
import uuid
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

from engine.core.config import EngineConfig
from engine.core.context import RequestContext

logger = logging.getLogger(__name__)

# Headers whose values must be replaced with [REDACTED]
_REDACTED_HEADERS: frozenset[str] = frozenset({
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "proxy-authorization",
})

# Body field names whose values must be redacted
_REDACTED_FIELDS: frozenset[str] = frozenset({
    "password",
    "passwd",
    "pass",
    "secret",
    "token",
    "api_key",
    "apikey",
    "api-key",
    "access_token",
    "refresh_token",
    "credit_card",
    "creditcard",
    "ssn",
    "social_security",
})

_DEFAULT_CONFIG = EngineConfig()


class RequestCollector:
    """Builds a safe, immutable RequestContext from raw request data."""

    def __init__(self, config: EngineConfig = _DEFAULT_CONFIG) -> None:
        self._config = config

    def collect(
        self,
        source_ip: str,
        method: str,
        raw_url: str,
        headers: dict[str, str],
        body: str = "",
    ) -> RequestContext:
        """Parse and sanitize raw request data into a RequestContext.

        Args:
            source_ip: The IP address from the TCP connection.
            method: HTTP method (GET, POST, etc.).
            raw_url: The raw request URL (path + query string).
            headers: Raw HTTP headers as a dict.
            body: Raw request body as a string.

        Returns:
            A frozen RequestContext safe for detectors.

        Raises:
            ValueError: If source_ip is not a valid IP address.
        """
        # 1. Validate source IP
        validated_ip = self._validate_ip(source_ip)

        # 2. Parse URL into path and query params
        parsed = urlsplit(raw_url)
        path = parsed.path or "/"
        query_params = self._parse_query(parsed.query)

        # 3. Truncate body to configured limit
        truncated_body = body[: self._config.max_body_bytes]

        # 4. Redact sensitive headers
        safe_headers = self._redact_headers(headers)

        # 5. Redact sensitive body fields
        safe_body = self._redact_body_fields(truncated_body)

        # 6. Build the immutable RequestContext
        return RequestContext(
            source_ip=validated_ip,
            method=method.upper(),
            path=path,
            query_params=query_params,
            headers=safe_headers,
            body=safe_body,
            timestamp=datetime.now(timezone.utc),
            request_id=str(uuid.uuid4()),
        )

    @staticmethod
    def _validate_ip(ip_str: str) -> str:
        """Validate and normalize an IP address string.

        Returns the normalized string form.
        Raises ValueError for invalid IPs.
        """
        addr = ipaddress.ip_address(ip_str.strip())
        return str(addr)

    @staticmethod
    def _parse_query(query_string: str) -> dict[str, str]:
        """Parse a query string into a flat dict (first value wins)."""
        parsed = parse_qs(query_string, keep_blank_values=True)
        # parse_qs returns lists; take the first value only
        return {k: v[0] for k, v in parsed.items()}

    @staticmethod
    def _redact_headers(headers: dict[str, str]) -> dict[str, str]:
        """Replace values of sensitive headers with [REDACTED]."""
        safe = {}
        for key, value in headers.items():
            if key.lower() in _REDACTED_HEADERS:
                safe[key] = "[REDACTED]"
            else:
                safe[key] = value
        return safe

    @staticmethod
    def _redact_body_fields(body: str) -> str:
        """Best-effort redaction of sensitive field values in the body.

        Handles simple key=value pairs and JSON-like patterns.
        This is not a full parser — it catches common patterns.
        """
        result = body
        for field_name in _REDACTED_FIELDS:
            # Handle URL-encoded form: password=secret123&
            import re

            # key=value in form data
            pattern_form = re.compile(
                rf"({re.escape(field_name)})=([^&\s]+)",
                re.IGNORECASE,
            )
            result = pattern_form.sub(rf"\1=[REDACTED]", result)

            # "key": "value" in JSON
            pattern_json = re.compile(
                rf'("{re.escape(field_name)}"\s*:\s*)"[^"]*"',
                re.IGNORECASE,
            )
            result = pattern_json.sub(rf'\1"[REDACTED]"', result)

        return result
```

---

#### `engine/detectors/directory_enum.py`
**Location:** `HoneyPot/engine/detectors/directory_enum.py`
**Purpose:** Detects requests to sensitive paths like `/.env`, `/.git/config`, `/wp-admin`, `/phpmyadmin`. Stateless — just matches the path against known sensitive paths.

**What it does (plain English):**
- When a request comes in, normalizes the path (using the normalizer)
- Checks if the path matches any "secret-bearing" paths (like `/.env`) → returns MEDIUM severity
- Checks if the path matches any "admin/tooling" paths (like `/admin`) → returns LOW severity
- If nothing matches, returns empty list (no detection)
- Confidence is never 1.0 — someone could genuinely mistype `/admin`

**Python concepts used:**
- Inheritance: extends `BaseDetector` (like `extends` in JavaScript classes)
- `@property` — getter method (like JS `get name() {}`)
- `in frozenset` — O(1) lookup (like `Set.has()` in JS)
- `.startswith(tuple)` — checks multiple prefixes at once

```python
"""Directory enumeration detector.

Flags requests to sensitive paths such as /.env, /.git/config,
/wp-admin, /phpmyadmin and /backup.zip. Stateless.
"""

from engine.core.config import EngineConfig
from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult, Severity
from engine.core.normalizer import normalize
from engine.detectors.base import BaseDetector
from engine.rules.signatures import (
    ADMIN_EXACT_PATHS,
    ADMIN_PREFIX_PATHS,
    SENSITIVE_EXACT_PATHS,
    SENSITIVE_PREFIX_PATHS,
)

_DEFAULT_CONFIG = EngineConfig()


class DirectoryEnumerationDetector(BaseDetector):
    """Detects requests to known sensitive or administrative paths."""

    description = "Flags requests to commonly scanned sensitive paths"
    version = "1.0"

    def __init__(self, config: EngineConfig = _DEFAULT_CONFIG) -> None:
        self._config = config

    @property
    def name(self) -> str:
        return "directory_enumeration"

    @property
    def category(self) -> AttackCategory:
        return AttackCategory.DIRECTORY_ENUMERATION

    def analyze(self, context: RequestContext) -> list[DetectionResult]:
        """Check if the request path matches known sensitive paths."""
        results: list[DetectionResult] = []

        # Normalize the path to defeat encoding tricks
        normalized_path = normalize(context.path, self._config)

        # Strip trailing slash for exact matching, but keep "/" as is
        check_path = normalized_path.rstrip("/") if normalized_path != "/" else "/"

        # Check 1: Secret-bearing exact paths (MEDIUM severity)
        if check_path in SENSITIVE_EXACT_PATHS or normalized_path in SENSITIVE_EXACT_PATHS:
            results.append(
                DetectionResult(
                    detector=self.name,
                    category=self.category,
                    severity=Severity.MEDIUM,
                    confidence=0.85,
                    reason="Request to a known secret-bearing path",
                    evidence=f"path={normalized_path[:200]}",
                )
            )
            return results

        # Check 2: Secret-bearing prefix paths (MEDIUM severity)
        if normalized_path.startswith(SENSITIVE_PREFIX_PATHS):
            results.append(
                DetectionResult(
                    detector=self.name,
                    category=self.category,
                    severity=Severity.MEDIUM,
                    confidence=0.80,
                    reason="Request to a known secret-bearing directory",
                    evidence=f"path={normalized_path[:200]}",
                )
            )
            return results

        # Check 3: Admin / tooling exact paths (LOW severity)
        if check_path in ADMIN_EXACT_PATHS or normalized_path in ADMIN_EXACT_PATHS:
            results.append(
                DetectionResult(
                    detector=self.name,
                    category=self.category,
                    severity=Severity.LOW,
                    confidence=0.70,
                    reason="Request to a known administrative or tooling path",
                    evidence=f"path={normalized_path[:200]}",
                )
            )
            return results

        # Check 4: Admin prefix paths (LOW severity)
        if normalized_path.startswith(ADMIN_PREFIX_PATHS):
            results.append(
                DetectionResult(
                    detector=self.name,
                    category=self.category,
                    severity=Severity.LOW,
                    confidence=0.65,
                    reason="Request to a known administrative directory",
                    evidence=f"path={normalized_path[:200]}",
                )
            )
            return results

        # No match — legitimate traffic
        return results
```

---

### Phase 3 Tests

**Location:** `HoneyPot/tests/unit/test_normalizer.py`, `HoneyPot/tests/unit/test_request_collector.py`, `HoneyPot/tests/unit/test_directory_enum.py`

Tests should cover:
1. **Normalizer:** Double-encoded paths decode correctly; null bytes removed; uppercase → lowercase; decode round limit respected
2. **Collector:** Valid `RequestContext` built; Authorization/Cookie headers redacted; password fields redacted; oversized body truncated; invalid IP raises `ValueError`
3. **Directory enumeration:**
   - **Must detect:** `/.env`, `/.git/config`, `/admin`, `/phpmyadmin`, `/%2eenv` (encoded), `/.ENV` (uppercase)
   - **Must NOT detect:** `/`, `/index.html`, `/login`, `/api/products`, `/about`, `/contact`

---

## Phase 4 — Injection Detectors

**Goal:** SQL injection and XSS detectors with encoding handling.
**Done when:** Samples detected, legitimate suite clean.
**Difficulty:** Medium | **Time:** ~3-4 days

### Files to create in this phase

---

#### `engine/detectors/sql_injection.py`
**Location:** `HoneyPot/engine/detectors/sql_injection.py`
**Purpose:** Decodes input repeatedly, then matches SQL patterns (UNION SELECT, OR 1=1, comments, stacked queries). Reports "suspicious pattern", never "successful injection".

**What it does:**
- Normalizes the path, every query param value, and body
- Runs regex patterns from `signatures.py` to look for SQL keywords and structures
- If matched, returns a `DetectionResult` with severity HIGH
- Must NOT flag normal text like "O'Brien" or "select a laptop"

```python
# To be implemented in Phase 4
# Key regex patterns to add to signatures.py:
#   - UNION\s+(ALL\s+)?SELECT
#   - OR\s+['"]?\d+['"]?\s*=\s*['"]?\d+
#   - ;\s*(DROP|DELETE|INSERT|UPDATE|ALTER)\s+
#   - --\s*$  or  /\*.*\*/
#   - '\s*OR\s+'
#   - SLEEP\(\d+\)  |  BENCHMARK\(
#   - WAITFOR\s+DELAY
#   - LOAD_FILE  |  INTO\s+(OUT|DUMP)FILE
```

---

#### `engine/detectors/xss.py`
**Location:** `HoneyPot/engine/detectors/xss.py`
**Purpose:** Matches `<script>`, event-handler attributes (`onerror=`, `onload=`), `javascript:` URLs including encoded variants.

**What it does:**
- Normalizes all input fields
- Matches HTML script injection patterns
- Severity: MEDIUM (the honeypot has no real users to attack)

```python
# To be implemented in Phase 4
# Key regex patterns to add to signatures.py:
#   - <script[\s>]
#   - </script>
#   - javascript\s*:
#   - on(error|load|click|mouseover|focus|blur)\s*=
#   - <iframe[\s>]
#   - <object[\s>]
#   - <embed[\s>]
#   - <svg[\s>].*on\w+=
#   - expression\s*\(
#   - vbscript\s*:
```

---

#### `engine/rules/signatures.py` *(update)*
**Location:** `HoneyPot/engine/rules/signatures.py`
**Purpose:** Add compiled regex patterns for SQL injection and XSS.

```python
# Phase 4 additions — compiled regexes
import re

# SQL injection patterns (compiled for performance)
SQL_INJECTION_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"union\s+(all\s+)?select", re.IGNORECASE),
    re.compile(r"or\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+", re.IGNORECASE),
    re.compile(r";\s*(drop|delete|insert|update|alter)\s+", re.IGNORECASE),
    re.compile(r"'\s*or\s+'", re.IGNORECASE),
    re.compile(r"sleep\s*\(\s*\d+\s*\)", re.IGNORECASE),
    re.compile(r"benchmark\s*\(", re.IGNORECASE),
    re.compile(r"waitfor\s+delay", re.IGNORECASE),
    re.compile(r"load_file\s*\(", re.IGNORECASE),
    re.compile(r"into\s+(out|dump)file", re.IGNORECASE),
    re.compile(r"(?:--|#|/\*)", re.IGNORECASE),
)

# XSS patterns
XSS_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"<script[\s>]", re.IGNORECASE),
    re.compile(r"</script>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on(error|load|click|mouseover|focus|blur|submit|change)\s*=", re.IGNORECASE),
    re.compile(r"<iframe[\s>]", re.IGNORECASE),
    re.compile(r"<object[\s>]", re.IGNORECASE),
    re.compile(r"<embed[\s>]", re.IGNORECASE),
    re.compile(r"<svg[^>]*\son\w+\s*=", re.IGNORECASE),
    re.compile(r"expression\s*\(", re.IGNORECASE),
    re.compile(r"vbscript\s*:", re.IGNORECASE),
)
```

---

## Phase 5 — More Detectors

**Goal:** Path traversal, command injection, suspicious request.
**Done when:** All detectors share the base contract and have test files.
**Difficulty:** Medium | **Time:** ~3-4 days

### Files to create in this phase

---

#### `engine/detectors/path_traversal.py`
**Location:** `HoneyPot/engine/detectors/path_traversal.py`
**Purpose:** Finds `../`, `..\`, and encoded forms (`%2e%2e%2f`, double encoding). Normalizes paths before matching. Severity: HIGH.

```python
# To be implemented in Phase 5
# Key patterns to add to signatures.py:
#   - \.\./     (literal ../)
#   - \.\.\\    (literal ..\)
#   - %2e%2e    (encoded ..)
#   - ..%2f     (mixed encoding)
#   - ..%5c     (mixed encoding with backslash)
#   - /etc/passwd, /etc/shadow, /windows/system32
```

---

#### `engine/detectors/command_injection.py`
**Location:** `HoneyPot/engine/detectors/command_injection.py`
**Purpose:** Finds shell separators (`;`, `&&`, `|`, backticks, `$()`) combined with command-like words. Never executes anything. Severity: HIGH.

```python
# To be implemented in Phase 5
# Key patterns to add to signatures.py:
#   - Shell operators: ;  &&  ||  |  `  $()
#   - Command words: cat, ls, pwd, whoami, id, uname, wget, curl, nc,
#                     bash, sh, python, perl, ruby, php, nslookup, ping
#   - Detection rule: operator + command word must both be present
```

---

#### `engine/detectors/suspicious_request.py`
**Location:** `HoneyPot/engine/detectors/suspicious_request.py`
**Purpose:** Flags malformed requests, missing/odd headers, oversized headers, unusual methods. Low confidence — metadata alone proves little. Severity: LOW.

```python
# To be implemented in Phase 5
# What to check:
#   - Missing Host header
#   - Unusual HTTP methods (TRACE, CONNECT, OPTIONS, PROPFIND, PATCH with no body)
#   - Oversized individual headers (> max_header_bytes)
#   - Known scanner User-Agents (sqlmap, nikto, nmap, dirbuster, gobuster, etc.)
#   - Control characters in headers
#   - Very long URL (> max_url_length)
```

---

#### `engine/rules/signatures.py` *(update)*
Add path traversal patterns, command injection patterns, and scanner User-Agent list.

---

## Phase 6 — Behaviour

**Goal:** Time-window stores, brute force, endpoint enumeration, behaviour analyzer, automation analyzer, session analyzer.
**Done when:** A scripted burst raises the right events and score; memory bounded.
**Difficulty:** Hard | **Time:** ~5-7 days

### Files to create in this phase

---

#### `engine/detectors/brute_force.py`
**Location:** `HoneyPot/engine/detectors/brute_force.py`
**Purpose:** Counts login attempts per IP in a sliding window. Flags when threshold crossed (default: 5 attempts per 60 seconds). **Stateful** — keeps per-IP counters in memory.

```python
# To be implemented in Phase 6
# Key concepts:
#   - collections.deque with maxlen for sliding window
#   - Tracks POST requests to login-like paths (/login, /wp-login.php, /admin/login)
#   - Per-IP deque of timestamps
#   - When count in window > brute_force_attempts → DetectionResult
#   - Bounded memory: max_tracked_sources IPs tracked, evict oldest when full
```

---

#### `engine/detectors/endpoint_enum.py`
**Location:** `HoneyPot/engine/detectors/endpoint_enum.py`
**Purpose:** Flags one IP requesting many distinct paths in a time window (default: 15 paths per 60 seconds). **Stateful** — uses per-IP deques.

```python
# To be implemented in Phase 6
# Key concepts:
#   - Per-IP deque of (path, timestamp) pairs
#   - Count distinct paths in the window
#   - Also count 404-like responses (many errors = likely enumeration)
#   - Two thresholds: distinct_paths and error_count
#   - Bounded memory like brute_force
```

---

#### `engine/analyzers/behavior.py`
**Location:** `HoneyPot/engine/analyzers/behavior.py`
**Purpose:** Correlates events per source IP over time. Tracks repeated categories, multiple attack types, sequential scanning. Produces a behavioural score (0–100).

```python
# To be implemented in Phase 6
# Score contributions (starting values):
#   - High request rate (60s window): +10 to +15
#   - Many distinct paths or many 404s (60s): +15 to +20
#   - Repeated login attempts (60s): +15 to +20
#   - Two+ attack categories from one source (10min): +15 to +20
#   - Repeated high-severity events (10min): +10 to +15
#   - Automation indicators (5min): +5 to +10
# Score bands: 0-29 low, 30-59 medium, 60-79 high, 80-100 very high
```

---

#### `engine/analyzers/automation.py`
**Location:** `HoneyPot/engine/analyzers/automation.py`
**Purpose:** Estimates automation likelihood from request timing, rate, and regularity. User-Agent is a weak hint only — a custom UA alone does NOT mark traffic as automated.

```python
# To be implemented in Phase 6
# Key signals:
#   - Regular interval between requests (low jitter → likely automated)
#   - Very high request rate
#   - Sequential path patterns (like wordlist order)
#   - Known scanner User-Agents (secondary hint only, not conclusive)
```

---

#### `engine/analyzers/session_analyzer.py`
**Location:** `HoneyPot/engine/analyzers/session_analyzer.py`
**Purpose:** Groups requests into sessions. A session = same IP + same cookie + gap < 30 minutes. Tracks per-session activity.

```python
# To be implemented in Phase 6
# Key concepts:
#   - Session grouping: IP + time gap (session_idle_gap_seconds, default 30 min)
#   - Cookie matching when available
#   - Track: request count, categories seen, paths visited, duration
#   - Bounded memory: max_tracked_sources
```

---

## Phase 7 — Honeypot Listener

**Goal:** Asyncio HTTP listener, strict parser, response simulator, event queue.
**Done when:** `curl` gets believable fake responses; limits enforced.
**Difficulty:** Hard | **Time:** ~4-6 days

### Files to create in this phase

---

#### `engine/server/http_server.py`
**Location:** `HoneyPot/engine/server/http_server.py`
**Purpose:** The decoy HTTP listener. Built on `asyncio.start_server` with request size limits and timeouts. Opens port 8080 for untrusted traffic.

```python
# To be implemented in Phase 7
# Key concepts:
#   - asyncio.start_server(handler, host, port)  — like http.createServer() in Node.js
#   - Apply read size limit (64 KB max)
#   - Apply read timeout (10 seconds)
#   - Max concurrent connections
#   - Start/stop lifecycle methods
```

---

#### `engine/server/request_handler.py`
**Location:** `HoneyPot/engine/server/request_handler.py`
**Purpose:** Per-connection logic. Reads raw bytes → calls collector → runs engine → passes results to processor → asks simulator for a fake response.

```python
# To be implemented in Phase 7
# Flow per connection:
#   1. Read raw bytes from reader (with timeout)
#   2. Parse HTTP request line (method, path, version)
#   3. Parse headers
#   4. Read body up to Content-Length (truncated to limit)
#   5. Call RequestCollector.collect() → RequestContext
#   6. Call DetectionEngine.analyze(ctx) → list[DetectionResult]
#   7. Call EventProcessor.process(ctx, results) → SecurityEvent or None
#   8. Call ResponseSimulator for a fake response
#   9. Write response bytes to writer
#   10. Close connection
```

---

#### `engine/server/response_simulator.py`
**Location:** `HoneyPot/engine/server/response_simulator.py`
**Purpose:** Returns pre-built fake HTTP responses. Fake login page, fake admin page, fake 403/404. Never reads from disk. Never executes request data.

```python
# To be implemented in Phase 7
# Key responses:
#   - /login → fake login HTML page (200)
#   - /admin → fake 403 Forbidden
#   - /wp-admin → fake WordPress login page (200)
#   - everything else → fake 404 Not Found
#   - All responses are pre-built byte strings, not templates
```

---

## Phase 8 — Storage

**Goal:** Models, connection, repository, EventSink, Alembic first migration. **Milestone 1:** Simulated attack becomes a database row.
**Done when:** Events persist and can be filtered and paged.
**Difficulty:** Medium | **Time:** ~3-4 days

### Files to create in this phase

---

#### `engine/events/storage_interface.py`
**Location:** `HoneyPot/engine/events/storage_interface.py`
**Purpose:** Abstract `EventSink` with one method: `save(event)`. The backend provides the SQLite implementation; tests provide an in-memory one.

```python
"""Abstract storage interface for security events.

The engine knows only this interface.
The backend provides a concrete implementation.
Tests provide an in-memory implementation.
"""

import abc

from engine.events.event import SecurityEvent


class EventSink(abc.ABC):
    @abc.abstractmethod
    async def save(self, event: SecurityEvent) -> None:
        """Persist or forward a security event.

        Must not raise exceptions that propagate to the detection engine.
        Must handle failures internally (log and continue).
        """
        raise NotImplementedError
```

---

#### `engine/events/event_processor.py`
**Location:** `HoneyPot/engine/events/event_processor.py`
**Purpose:** Merges detector results + analyzer output into one normalized `SecurityEvent`. Generates UUID, picks the final category and severity. Calls `sink.save()`. **This is the only place classification happens.**

```python
# To be implemented in Phase 8
# Flow:
#   1. If results list is empty → return None (normal traffic)
#   2. Find the dominant result (highest severity, then highest confidence)
#   3. Average confidence across all results
#   4. Collect all detection reasons
#   5. Collect all evidence (truncated)
#   6. Run behavior.score(ip) → behavioral_score
#   7. Run automation.likelihood(ip, ua) → automation_likelihood
#   8. Run session.process(ip, cookie) → session_id
#   9. Build SecurityEvent with uuid4, all merged fields
#   10. Call await sink.save(event)
#   11. Return the event (even if save fails — save failure ≠ detection failure)
```

---

#### `backend/database/connection.py`
**Location:** `HoneyPot/backend/database/connection.py`
**Purpose:** SQLAlchemy async engine and session factory. Configures SQLite WAL mode, busy timeout, and foreign keys.

```python
# To be implemented in Phase 8
# Key setup:
#   - create_async_engine("sqlite+aiosqlite:///data/database/honeypot.db")
#   - WAL mode: execute "PRAGMA journal_mode=WAL"
#   - Busy timeout: execute "PRAGMA busy_timeout=5000"
#   - Foreign keys: execute "PRAGMA foreign_keys=ON"
#   - AsyncSession factory
#   - get_db() dependency for FastAPI
```

---

#### `backend/database/models.py`
**Location:** `HoneyPot/backend/database/models.py`
**Purpose:** SQLAlchemy ORM table definitions.

```python
# To be implemented in Phase 8
# Tables:
#   - security_events: id, event_uid, created_at, source_ip, category, severity,
#     confidence, method, path, target, summary, request_id, evidence (JSON text)
#   - detection_results: id, event_id (FK), detector, category, severity,
#     confidence, reason, evidence
#   - source_observations: source_ip (PK), first_seen, last_seen, total_requests,
#     total_events, categories_seen (JSON), latest_behavior_score
#   - analyst_annotations: id, event_id (FK), analyst, note, created_at
#   - audit_log: id, action, details (JSON), created_at
```

---

#### `backend/database/repository.py`
**Location:** `HoneyPot/backend/database/repository.py`
**Purpose:** All database queries: create, filter, paginate, aggregate, timeline, source observation upsert.

```python
# To be implemented in Phase 8
# Classes:
#   EventRepository — create, get_by_id, list (with filters, pagination, sort),
#     count_by_severity, count_by_category, timeline, top_targets, top_sources
#   SourceRepository — upsert (create or update source observations),
#     get_by_ip, list_all, get_events_for_source
```

---

## Phase 9 — REST API

**Goal:** Routes, schemas, auth, statistics, attackers.
**Done when:** All endpoints tested with a temporary database.
**Difficulty:** Medium | **Time:** ~3-5 days

### Files to create in this phase

| File | Location | Purpose |
|------|----------|---------|
| `backend/config.py` | `HoneyPot/backend/config.py` | Loads settings from `.env` using pydantic-settings |
| `backend/auth.py` | `HoneyPot/backend/auth.py` | API key verification with constant-time comparison |
| `backend/api/dependencies.py` | `HoneyPot/backend/api/dependencies.py` | Shared FastAPI dependencies: DB session and auth |
| `backend/api/routes/health.py` | `HoneyPot/backend/api/routes/health.py` | `GET /api/health` — no auth required |
| `backend/api/routes/events.py` | `HoneyPot/backend/api/routes/events.py` | `GET /api/events`, `GET /api/events/{id}`, annotations |
| `backend/api/routes/attackers.py` | `HoneyPot/backend/api/routes/attackers.py` | `GET /api/attackers`, `GET /api/attackers/{ip}` |
| `backend/api/routes/statistics.py` | `HoneyPot/backend/api/routes/statistics.py` | `GET /api/statistics` with time range |
| `backend/api/routes/detectors.py` | `HoneyPot/backend/api/routes/detectors.py` | `GET /api/detectors` — registered detector list |
| `backend/api/routes/system.py` | `HoneyPot/backend/api/routes/system.py` | `GET /api/system/status` |
| `backend/schemas/event.py` | `HoneyPot/backend/schemas/event.py` | Pydantic request/response models for events |
| `backend/schemas/attacker.py` | `HoneyPot/backend/schemas/attacker.py` | Pydantic models for attacker/source data |
| `backend/schemas/statistics.py` | `HoneyPot/backend/schemas/statistics.py` | Pydantic models for statistics responses |
| `backend/main.py` | `HoneyPot/backend/main.py` | FastAPI app creation, router registration, lifespan |

---

## Phase 10 — Live Feed

**Goal:** WebSocket manager, polling task, client authentication.
**Done when:** A new event reaches a test client within seconds.
**Difficulty:** Medium | **Time:** ~2-3 days

### Files to create in this phase

| File | Location | Purpose |
|------|----------|---------|
| `backend/services/ws_manager.py` | `HoneyPot/backend/services/ws_manager.py` | Tracks connected WebSocket clients, broadcasts safely |
| `backend/services/live_feed.py` | `HoneyPot/backend/services/live_feed.py` | Background task: polls DB for new rows, passes to ws_manager |
| `backend/services/event_service.py` | `HoneyPot/backend/services/event_service.py` | Runs repository save, then broadcasts through WebSocket manager |
| `backend/api/websockets/events.py` | `HoneyPot/backend/api/websockets/events.py` | `/ws/events` endpoint, authenticates, streams events |
| `backend/integration/event_sink.py` | `HoneyPot/backend/integration/event_sink.py` | `BackendEventSink` — implements `EventSink`, puts events in queue |
| `backend/integration/event_mapper.py` | `HoneyPot/backend/integration/event_mapper.py` | Converts `SecurityEvent` → plain dict for database |
| `backend/integration/engine_adapter.py` | `HoneyPot/backend/integration/engine_adapter.py` | Owns the asyncio.Queue + worker task |

---

## Phase 11 — Dashboard

**Goal:** Layout, five pages, hooks, charts, states. **Milestone 2:** End-to-end demo.
**Done when:** Attack script causes visible live and historical data.
**Difficulty:** Medium-Hard | **Time:** ~7-10 days

### Files to create in this phase

| File | Location | Purpose |
|------|----------|---------|
| `frontend/src/App.jsx` | `HoneyPot/frontend/src/App.jsx` | Router setup, auth guard |
| `frontend/src/services/api.js` | `HoneyPot/frontend/src/services/api.js` | Shared fetch client with auth header |
| `frontend/src/services/eventsApi.js` | `HoneyPot/frontend/src/services/eventsApi.js` | `getEvents()`, `getEvent()` |
| `frontend/src/services/attackersApi.js` | `HoneyPot/frontend/src/services/attackersApi.js` | `getAttackers()`, `getAttacker()` |
| `frontend/src/services/statisticsApi.js` | `HoneyPot/frontend/src/services/statisticsApi.js` | `getStatistics()`, `getTimeline()` |
| `frontend/src/services/detectorsApi.js` | `HoneyPot/frontend/src/services/detectorsApi.js` | `getDetectors()` |
| `frontend/src/services/systemApi.js` | `HoneyPot/frontend/src/services/systemApi.js` | `getStatus()` |
| `frontend/src/services/websocket.js` | `HoneyPot/frontend/src/services/websocket.js` | WebSocket client with auto-reconnect |
| `frontend/src/hooks/useWebSocket.js` | `HoneyPot/frontend/src/hooks/useWebSocket.js` | React hook wrapping WebSocket |
| `frontend/src/hooks/useAuth.js` | `HoneyPot/frontend/src/hooks/useAuth.js` | API key management |
| `frontend/src/hooks/useEvents.js` | `HoneyPot/frontend/src/hooks/useEvents.js` | Paginated events with filters |
| `frontend/src/hooks/useStatistics.js` | `HoneyPot/frontend/src/hooks/useStatistics.js` | Stats with periodic refresh |
| `frontend/src/pages/Login.jsx` | `HoneyPot/frontend/src/pages/Login.jsx` | API key entry screen |
| `frontend/src/pages/Dashboard.jsx` | `HoneyPot/frontend/src/pages/Dashboard.jsx` | Overview with stat cards, charts |
| `frontend/src/pages/LiveMonitor.jsx` | `HoneyPot/frontend/src/pages/LiveMonitor.jsx` | Real-time event stream |
| `frontend/src/pages/EventsExplorer.jsx` | `HoneyPot/frontend/src/pages/EventsExplorer.jsx` | Event table with search, filters, pagination |
| `frontend/src/pages/EventDetail.jsx` | `HoneyPot/frontend/src/pages/EventDetail.jsx` | Full event detail view |
| `frontend/src/pages/SourceIntelligence.jsx` | `HoneyPot/frontend/src/pages/SourceIntelligence.jsx` | List of observed IPs |
| `frontend/src/pages/SourceDetail.jsx` | `HoneyPot/frontend/src/pages/SourceDetail.jsx` | Per-IP stats and event history |
| `frontend/src/pages/ThreatAnalytics.jsx` | `HoneyPot/frontend/src/pages/ThreatAnalytics.jsx` | Charts: trends, top endpoints |
| `frontend/src/pages/DetectionRules.jsx` | `HoneyPot/frontend/src/pages/DetectionRules.jsx` | Registered detectors list |
| `frontend/src/pages/SystemSettings.jsx` | `HoneyPot/frontend/src/pages/SystemSettings.jsx` | Engine/DB/queue status |
| `frontend/src/components/layout/Sidebar.jsx` | `HoneyPot/frontend/src/components/layout/Sidebar.jsx` | Navigation menu |
| `frontend/src/components/layout/TopNav.jsx` | `HoneyPot/frontend/src/components/layout/TopNav.jsx` | Page title + WS status |
| `frontend/src/components/layout/Layout.jsx` | `HoneyPot/frontend/src/components/layout/Layout.jsx` | Sidebar + TopNav + content |
| `frontend/src/components/ui/Badge.jsx` | `HoneyPot/frontend/src/components/ui/Badge.jsx` | Severity/category badges |
| `frontend/src/components/ui/Card.jsx` | `HoneyPot/frontend/src/components/ui/Card.jsx` | Stat card with number, label, icon |
| `frontend/src/components/ui/DataTable.jsx` | `HoneyPot/frontend/src/components/ui/DataTable.jsx` | Sortable, paginated table |
| `frontend/src/components/ui/Spinner.jsx` | `HoneyPot/frontend/src/components/ui/Spinner.jsx` | Loading spinner |
| `frontend/src/components/ui/EmptyState.jsx` | `HoneyPot/frontend/src/components/ui/EmptyState.jsx` | "No data yet" placeholder |
| `frontend/src/components/ui/ErrorState.jsx` | `HoneyPot/frontend/src/components/ui/ErrorState.jsx` | Error display with retry button |
| `frontend/src/utils/formatters.js` | `HoneyPot/frontend/src/utils/formatters.js` | Date, severity, category formatters |
| `frontend/src/utils/severity.js` | `HoneyPot/frontend/src/utils/severity.js` | Severity → color mapping |
| `frontend/src/utils/constants.js` | `HoneyPot/frontend/src/utils/constants.js` | Display names for categories and severities |

---

## Phase 12 — Network Monitor

**Goal:** Decoy ports, connection logging, port-scan detector.
**Done when:** Local scan against `127.0.0.1` produces one event.
**Difficulty:** Medium | **Time:** ~3-4 days

### Files to create in this phase

| File | Location | Purpose |
|------|----------|---------|
| `engine/network/ip_utils.py` | `HoneyPot/engine/network/ip_utils.py` | IP validation, private/public classification, normalization |
| `engine/network/connection_monitor.py` | `HoneyPot/engine/network/connection_monitor.py` | asyncio listeners on decoy TCP ports (2222, 2121, 3307, 8081). Logs connections without serving content |
| `engine/network/port_scan_detector.py` | `HoneyPot/engine/network/port_scan_detector.py` | Flags one IP hitting many different decoy ports within a window (default: 5 ports in 30 seconds) |

---

## Phase 13 — Hardening

**Goal:** Limits, redaction audit, systemd units, firewall file, VM trial, security tests.
**Done when:** Section 13.4 checklist satisfied.
**Difficulty:** Hard | **Time:** ~4-6 days

### Files to create in this phase

| File | Location | Purpose |
|------|----------|---------|
| `deploy/honeypot.service` | `HoneyPot/deploy/honeypot.service` | systemd unit for honeypot process with sandboxing |
| `deploy/management.service` | `HoneyPot/deploy/management.service` | systemd unit for management API |
| `deploy/nftables.conf` | `HoneyPot/deploy/nftables.conf` | Firewall rules: allow decoy ports, restrict management |
| `scripts/prune_old_events.py` | `HoneyPot/scripts/prune_old_events.py` | Deletes events older than retention period |
| `tests/security/` | `HoneyPot/tests/security/` | Security tests: no execution paths, redaction verified, limits enforced |

### Checklist before any exposure beyond localhost
- [ ] All security tests pass
- [ ] Legitimate-traffic suite shows acceptable false positives
- [ ] Runs in a VM as an unprivileged user with systemd limits and firewall
- [ ] Outbound traffic restricted; management API unreachable from outside
- [ ] No real credentials on the machine; database permissions verified
- [ ] Retention job working

---

## Phase 14 — Final Polish

**Goal:** Complete docs, diagrams, demo scenarios and screenshots. **Milestone 3:** Portfolio-ready.
**Done when:** A newcomer can set up and run it from the README.
**Difficulty:** Easy-Medium | **Time:** ~3-5 days

### Files to create in this phase

| File | Location | Purpose |
|------|----------|---------|
| `README.md` | `HoneyPot/README.md` | Complete setup guide with screenshots |
| `docs/architecture.md` | `HoneyPot/docs/architecture.md` | Architecture diagrams and explanation |
| `docs/api-documentation.md` | `HoneyPot/docs/api-documentation.md` | Full API reference |
| `docs/detection-rules.md` | `HoneyPot/docs/detection-rules.md` | Detector documentation with known limits |
| `docs/security-isolation.md` | `HoneyPot/docs/security-isolation.md` | Security design and threat model |
| `scripts/run_honeypot.py` | `HoneyPot/scripts/run_honeypot.py` | Composition root: loads settings, builds engine, starts listener |
| `scripts/simulate_attacks.py` | `HoneyPot/scripts/simulate_attacks.py` | Named attack scenarios for demos and testing |
| `scripts/seed_demo_data.py` | `HoneyPot/scripts/seed_demo_data.py` | Fills DB with fake events for dashboard testing |

---

## Phase 15 — Future Work (Optional)

**Goal:** Threat intelligence and extras.
**Difficulty:** Varies | **Time:** Open

| Feature | Technology | Benefit |
|---------|-----------|---------|
| IP Reputation | AbuseIPDB (free tier) | Adds context to sources in dashboard |
| VirusTotal | VirusTotal API | URL and domain reputation |
| GeoIP | Offline GeoIP database | Country maps and charts |
| MITRE ATT&CK | ATT&CK catalogue | Tag categories with technique IDs |
| YARA | YARA rules | File/payload pattern matching |
| STIX / TAXII | Threat data sharing | Export/import indicators |
| More decoys | SSH, FTP fake banners | Broader coverage |
| Alerts | Email or Telegram | Real-time notifications |
| TLS | Reverse proxy (nginx) | HTTPS support |

---

## Quick Reference — All Engine Files

| File | Phase | Status |
|------|-------|--------|
| `engine/core/config.py` | 2 | ✅ Done |
| `engine/core/context.py` | 2 | ✅ Done |
| `engine/core/detection.py` | 2 | ✅ Done |
| `engine/core/engine.py` | 2 | ✅ Done |
| `engine/detectors/base.py` | 2 | ✅ Done |
| `engine/events/event.py` | 2 | ✅ Done |
| `engine/core/normalizer.py` | 3 | 🔄 Current |
| `engine/collectors/request_collector.py` | 3 | 🔄 Current |
| `engine/rules/signatures.py` | 3 | 🔄 Current |
| `engine/detectors/directory_enum.py` | 3 | 🔄 Current |
| `engine/detectors/sql_injection.py` | 4 | ⬜ Pending |
| `engine/detectors/xss.py` | 4 | ⬜ Pending |
| `engine/detectors/path_traversal.py` | 5 | ⬜ Pending |
| `engine/detectors/command_injection.py` | 5 | ⬜ Pending |
| `engine/detectors/suspicious_request.py` | 5 | ⬜ Pending |
| `engine/detectors/brute_force.py` | 6 | ⬜ Pending |
| `engine/detectors/endpoint_enum.py` | 6 | ⬜ Pending |
| `engine/analyzers/behavior.py` | 6 | ⬜ Pending |
| `engine/analyzers/automation.py` | 6 | ⬜ Pending |
| `engine/analyzers/session_analyzer.py` | 6 | ⬜ Pending |
| `engine/server/http_server.py` | 7 | ⬜ Pending |
| `engine/server/request_handler.py` | 7 | ⬜ Pending |
| `engine/server/response_simulator.py` | 7 | ⬜ Pending |
| `engine/events/storage_interface.py` | 8 | ⬜ Pending |
| `engine/events/event_processor.py` | 8 | ⬜ Pending |
| `engine/network/ip_utils.py` | 12 | ⬜ Pending |
| `engine/network/connection_monitor.py` | 12 | ⬜ Pending |
| `engine/network/port_scan_detector.py` | 12 | ⬜ Pending |
