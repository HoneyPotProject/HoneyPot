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