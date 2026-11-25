# Flags requests to sensitive paths such as /.env, /.git/config, /wp-admin,
# /phpmyadmin and /backup.zip. Stateless.

from __future__ import annotations

from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult, Severity
from engine.detectors.base import BaseDetector
from engine.rules.signatures import SENSITIVE_PATH_PREFIXES, SENSITIVE_PATHS


class DirectoryEnumerationDetector(BaseDetector):
    name = 'DirectoryEnumerationDetector'
    category = AttackCategory.DIRECTORY_ENUMERATION
    description = 'Flags requests to well-known sensitive or administrative paths.'

    def analyze(self, ctx: RequestContext) -> list[DetectionResult]:
        path = (ctx.path or '/').lower()
        hit = path in {p.lower() for p in SENSITIVE_PATHS}
        prefix = any(path.startswith(p.lower()) for p in SENSITIVE_PATH_PREFIXES)
        if not hit and not prefix:
            return []
        return [
            DetectionResult(
                detector_name=self.name,
                category=self.category,
                severity=Severity.MEDIUM,
                confidence=0.7,
                reason=f'Request targeted a sensitive path: {ctx.path}',
                evidence={'path': ctx.path},
            )
        ]
