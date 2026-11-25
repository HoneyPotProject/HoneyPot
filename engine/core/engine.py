# DetectionEngine. Registers detectors, runs them on each RequestContext,
# wraps each in try/except so one crash never stops the others, and returns
# the list of results.

from __future__ import annotations

import logging
from typing import Iterable

from engine.core.context import RequestContext
from engine.core.detection import DetectionResult
from engine.detectors.base import BaseDetector

logger = logging.getLogger(__name__)


class DetectionEngine:
    """Runs every registered detector against a RequestContext."""

    def __init__(self) -> None:
        self._detectors: list[BaseDetector] = []
        self._running: bool = False

    @property
    def detectors(self) -> list[BaseDetector]:
        return list(self._detectors)

    @property
    def running(self) -> bool:
        return self._running

    def mark_running(self, value: bool) -> None:
        self._running = value

    def register(self, detector: BaseDetector) -> None:
        self._detectors.append(detector)

    def register_all(self, detectors: Iterable[BaseDetector]) -> None:
        for detector in detectors:
            self.register(detector)

    def analyze(self, ctx: RequestContext) -> list[DetectionResult]:
        results: list[DetectionResult] = []
        for detector in self._detectors:
            if not getattr(detector, 'enabled', True):
                continue
            try:
                found = detector.analyze(ctx) or []
            except Exception:
                logger.exception(
                    'Detector %s failed; continuing with remaining detectors',
                    getattr(detector, 'name', type(detector).__name__),
                )
                continue
            if found:
                detector.detection_count += len(found)
                results.extend(found)
        return results
