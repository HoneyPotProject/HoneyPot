# Person 2 — Detection Engine & Normalizer (Owner B)

This document contains the complete implementation for **Person 2 (Owner B)** across Phase 2 and Phase 3, including the exact file locations in the repository.

---

## Phase 2 — Detection Engine

### Restrictions Checklist
- No database imports
- No FastAPI imports
- No network requests
- No dashboard/frontend dependencies
- No actual attack-detection rules implemented

### 1. `engine/detectors/base.py`

**Actual file location:** `C:\honeypot\HoneyPot\engine\detectors\base.py` (relative path: `engine/detectors/base.py`)

```python
"""Abstract base class for all honeypot security detectors."""

from abc import ABC, abstractmethod

from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult


class BaseDetector(ABC):
    """Interface that every security detector must implement.

    Subclasses must define ``name`` and ``category`` attributes and implement
    :meth:`analyze`.
    """

    name: str
    category: AttackCategory

    def __init__(self) -> None:
        self.enabled: bool = True
        self.detection_count: int = 0

    @abstractmethod
    def analyze(self, context: RequestContext) -> list[DetectionResult]:
        """Inspect a single immutable RequestContext.

        Returns zero or more DetectionResult objects. Detectors must never
        mutate the context or execute attacker-controlled input.
        """
```

### 2. `engine/core/engine.py`

**Actual file location:** `C:\honeypot\HoneyPot\engine\core\engine.py` (relative path: `engine/core/engine.py`)

```python
"""Detection engine that registers detectors and runs them safely."""

import logging

from engine.core.context import RequestContext
from engine.core.detection import DetectionResult
from engine.detectors.base import BaseDetector

logger = logging.getLogger(__name__)


class DetectionEngine:
    """Executes registered detectors against a RequestContext with fault isolation."""

    def __init__(self) -> None:
        self._detectors: dict[str, BaseDetector] = {}

    @property
    def detectors(self) -> list[BaseDetector]:
        """Return a snapshot list of all registered detectors in registration order."""
        return list(self._detectors.values())

    def register_detector(self, detector: BaseDetector) -> None:
        """Register a BaseDetector instance.

        Raises:
            TypeError: If ``detector`` is not an instance of ``BaseDetector``.
            ValueError: If a detector with the same ``name`` is already registered.
        """
        if not isinstance(detector, BaseDetector):
            raise TypeError(
                f"Expected a BaseDetector instance, got {type(detector).__name__}"
            )
        if not getattr(detector, "name", None):
            raise ValueError("Detector must define a non-empty 'name' attribute")
        if detector.name in self._detectors:
            raise ValueError(
                f"Detector with name {detector.name!r} is already registered"
            )
        self._detectors[detector.name] = detector

    def unregister_detector(self, name: str) -> None:
        """Remove a registered detector by name if present."""
        self._detectors.pop(name, None)

    def get_detector(self, name: str) -> BaseDetector | None:
        """Return a registered detector by name, or None if not found."""
        return self._detectors.get(name)

    def analyze(self, context: RequestContext) -> list[DetectionResult]:
        """Run all enabled detectors against ``context`` and collect results.

        If a detector raises an exception, the failure is logged and isolated
        so remaining detectors continue to run.
        """
        collected: list[DetectionResult] = []

        for detector in self._detectors.values():
            if not detector.enabled:
                continue

            try:
                results = detector.analyze(context)
            except Exception:
                logger.exception(
                    "Detector %r failed while analyzing request_id=%s",
                    detector.name,
                    getattr(context, "request_id", "unknown"),
                )
                continue

            if results:
                detector.detection_count += len(results)
                collected.extend(results)

        return collected
```

---

## Phase 3 — Normalizer (`feature/phase3-normalizer`)

### 3. `engine/core/normalizer.py`

**Actual file location:** `C:\honeypot\HoneyPot\engine\core\normalizer.py` (relative path: `engine/core/normalizer.py`)

```python
"""Shared input normalization for honeypot detectors."""

import re
import unicodedata
from urllib.parse import unquote, unquote_plus

MAX_INPUT_LENGTH = 8_192
_WHITESPACE_RE = re.compile(r"\s+")


def normalize(
    value: str,
    *,
    max_rounds: int = 3,
    plus_as_space: bool = False,
) -> str:
    """Normalize untrusted text into a standard form for pattern matching.

    Steps:
    1. Bound input length to ``MAX_INPUT_LENGTH`` characters.
    2. URL-decode repeatedly until stable or ``max_rounds`` is reached.
    3. Strip null bytes (``\\x00``).
    4. Apply Unicode NFKC normalization.
    5. Collapse whitespace runs to a single space and lowercase.
    6. When ``plus_as_space`` is True, decode ``+`` as space (form data).

    Never resolves ``..``, never raises on strange input, and performs no I/O.
    """
    if not value:
        return ""
    if not isinstance(value, str):
        value = str(value)

    text = value[:MAX_INPUT_LENGTH]

    decoder = unquote_plus if plus_as_space else unquote
    for _ in range(max(0, max_rounds)):
        decoded = decoder(text)
        if decoded == text:
            break
        text = decoded

    text = text.replace("\x00", "")
    text = unicodedata.normalize("NFKC", text)
    text = _WHITESPACE_RE.sub(" ", text).lower()
    return text
```

### 4. `tests/engine/test_normalizer.py`

**Actual file location:** `C:\honeypot\HoneyPot\tests\engine\test_normalizer.py` (relative path: `tests/engine/test_normalizer.py`)

```python
import time

from engine.core.normalizer import MAX_INPUT_LENGTH, normalize


def test_single_and_double_url_decoding():
    assert normalize("%2e%2e%2f") == "../"
    assert normalize("%252e%252e%252f") == "../"


def test_round_limit_stops_deep_encoding():
    # 10-times URL-encoded "." (%2e -> %252e -> ... -> %25...2e)
    encoded = "."
    for _ in range(10):
        encoded = encoded.replace("%", "%25").replace(".", "%2e")

    result = normalize(encoded, max_rounds=3)
    assert result != "."
    assert "%" in result


def test_null_bytes_removed():
    assert normalize("admin\x00.php") == "admin.php"
    assert normalize("admin%00.php") == "admin.php"
    assert normalize("admin%2500.php") == "admin.php"


def test_unicode_nfkc_fullwidth_slash():
    assert normalize("\uff0fetc\uff0fpasswd") == "/etc/passwd"


def test_lowercase_and_whitespace_collapsed():
    assert normalize("UNION   \t\n  SELECT   1") == "union select 1"


def test_plus_as_space():
    assert normalize("select+1+from+users", plus_as_space=False) == "select+1+from+users"
    assert normalize("select+1+from+users", plus_as_space=True) == "select 1 from users"


def test_dot_dot_preserved():
    assert normalize("/static/../../etc/passwd") == "/static/../../etc/passwd"
    assert normalize("%2e%2e/%2e%2e/etc/passwd") == "../../etc/passwd"


def test_empty_string_and_strange_inputs():
    assert normalize("") == ""
    assert normalize("%ZZ%invalid%") == "%zz%invalid%"
    assert normalize(None) == ""  # type: ignore[arg-type]


def test_huge_input_bounded_and_fast():
    huge = "A" * 1_000_000
    start = time.perf_counter()
    result = normalize(huge)
    elapsed = time.perf_counter() - start

    assert len(result) == MAX_INPUT_LENGTH
    assert result == "a" * MAX_INPUT_LENGTH
    assert elapsed < 0.5
```
