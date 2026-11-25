# Matches <script>, event-handler attributes, javascript: URLs and encoded variants.

from __future__ import annotations

from engine.collectors.request_collector import multi_decode
from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult, Severity
from engine.detectors.base import BaseDetector
from engine.rules.signatures import XSS_PATTERNS


class XSSDetector(BaseDetector):
    name = 'XSSDetector'
    category = AttackCategory.XSS
    description = 'Flags script tags, event handlers, and javascript: URLs.'

    def analyze(self, ctx: RequestContext) -> list[DetectionResult]:
        text = multi_decode(self._haystack(ctx))
        matches = [p.pattern for p in XSS_PATTERNS if p.search(text)]
        if not matches:
            return []
        return [
            DetectionResult(
                detector_name=self.name,
                category=self.category,
                severity=Severity.HIGH,
                confidence=0.78,
                reason='Suspicious cross-site scripting pattern',
                evidence={'matched_patterns': matches[:5]},
            )
        ]
