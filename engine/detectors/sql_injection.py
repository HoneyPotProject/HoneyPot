# Decodes input repeatedly, then matches SQL patterns (UNION SELECT, OR 1=1,
# comments, stacked queries). Reports "suspicious pattern", never
# "successful injection".

from __future__ import annotations

from engine.collectors.request_collector import multi_decode
from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult, Severity
from engine.detectors.base import BaseDetector
from engine.rules.signatures import SQL_PATTERNS


class SQLInjectionDetector(BaseDetector):
    name = 'SQLInjectionDetector'
    category = AttackCategory.SQL_INJECTION
    description = 'Flags suspicious SQL syntax in paths, query strings, and bodies.'

    def analyze(self, ctx: RequestContext) -> list[DetectionResult]:
        text = multi_decode(self._haystack(ctx))
        matches = [p.pattern for p in SQL_PATTERNS if p.search(text)]
        if not matches:
            return []
        return [
            DetectionResult(
                detector_name=self.name,
                category=self.category,
                severity=Severity.HIGH,
                confidence=0.82,
                reason='Suspicious SQL pattern in request input',
                evidence={'matched_patterns': matches[:5]},
            )
        ]
