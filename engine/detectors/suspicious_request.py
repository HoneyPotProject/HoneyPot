# Flags malformed requests, missing or odd headers, oversized headers and
# unusual methods. Uses low confidence, since headers alone prove little.

from __future__ import annotations

from engine.core.config import DEFAULT_CONFIG, EngineConfig
from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult, Severity
from engine.detectors.base import BaseDetector
from engine.rules.signatures import STANDARD_METHODS, UNUSUAL_METHODS


class SuspiciousRequestDetector(BaseDetector):
    name = 'SuspiciousRequestDetector'
    category = AttackCategory.SUSPICIOUS_REQUEST
    description = 'Flags malformed HTTP, unusual methods, and odd header sets.'

    def __init__(self, config: EngineConfig | None = None) -> None:
        self._config = config or DEFAULT_CONFIG

    def analyze(self, ctx: RequestContext) -> list[DetectionResult]:
        reasons: list[str] = []
        if ctx.malformed:
            reasons.append('Malformed HTTP request')
        if ctx.method in UNUSUAL_METHODS or ctx.method not in STANDARD_METHODS:
            reasons.append(f'Unusual HTTP method: {ctx.method}')
        if 'host' not in ctx.headers and ctx.method in STANDARD_METHODS:
            reasons.append('Missing Host header')
        oversized = [
            name for name, value in ctx.headers.items()
            if len(value) > self._config.max_header_bytes
        ]
        if oversized:
            reasons.append('Oversized header values')
        if ctx.raw_size >= self._config.max_request_bytes:
            reasons.append('Request reached size limit')
        if not reasons:
            return []
        return [
            DetectionResult(
                detector_name=self.name,
                category=self.category,
                severity=Severity.LOW,
                confidence=0.4,
                reason='; '.join(reasons),
                evidence={'reasons': reasons},
            )
        ]
