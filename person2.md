# Person 2 — Detection Engine (Owner B)

This document contains the complete implementation for **Person 2 — Detection Engine**, including the exact file locations in the repository.

---

## Restrictions Checklist
- No database imports
- No FastAPI imports
- No network requests
- No dashboard/frontend dependencies
- No actual attack-detection rules implemented

---

## 1. `engine/detectors/base.py`

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

---

## 2. `engine/core/engine.py`

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

## 3. Deliverable Verification (Dummy Detector Example)

You can verify the deliverable by registering a dummy detector and running it through `DetectionEngine`:

```python
from datetime import UTC, datetime

from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult, Severity
from engine.core.engine import DetectionEngine
from engine.detectors.base import BaseDetector


class DummyDetector(BaseDetector):
    name = "dummy"
    category = AttackCategory.SUSPICIOUS_REQUEST

    def analyze(self, context: RequestContext) -> list[DetectionResult]:
        return [
            DetectionResult(
                detector=self.name,
                category=self.category,
                severity=Severity.LOW,
                confidence=0.5,
                reason="Dummy detection for engine verification",
                evidence=context.path,
            )
        ]


engine = DetectionEngine()
engine.register_detector(DummyDetector())

ctx = RequestContext(
    source_ip="127.0.0.1",
    method="GET",
    path="/test",
    query_params={},
    headers={"host": "localhost"},
    body="",
    timestamp=datetime.now(UTC),
    request_id="req-001",
)

results = engine.analyze(ctx)
print(results)
```

> **Note:** In `tests/engine/test_detector_base.py` and `tests/engine/test_engine.py`, the test suite already validates `BaseDetector` abstractness, `DetectionEngine.register_detector`, duplicate/type validation, `enabled` toggling, `detection_count` tracking, and crash isolation.
