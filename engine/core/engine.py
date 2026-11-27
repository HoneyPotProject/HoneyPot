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
