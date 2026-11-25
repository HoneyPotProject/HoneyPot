# Finds ../, ..\, and single, double and unicode-encoded forms.
# Normalizes paths before matching.

from __future__ import annotations

from engine.collectors.request_collector import multi_decode
from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult, Severity
from engine.detectors.base import BaseDetector
from engine.rules.signatures import PATH_TRAVERSAL_PATTERNS


class PathTraversalDetector(BaseDetector):
    name = 'PathTraversalDetector'
    category = AttackCategory.PATH_TRAVERSAL
    description = 'Flags directory traversal sequences in the request target.'

    def analyze(self, ctx: RequestContext) -> list[DetectionResult]:
        text = multi_decode(self._haystack(ctx))
        matches = [p.pattern for p in PATH_TRAVERSAL_PATTERNS if p.search(text)]
        if not matches:
            return []
        return [
            DetectionResult(
                detector_name=self.name,
                category=self.category,
                severity=Severity.HIGH,
                confidence=0.8,
                reason='Suspicious path traversal pattern',
                evidence={'matched_patterns': matches[:5]},
            )
        ]
