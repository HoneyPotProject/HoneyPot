# Finds shell separators (;, &&, |, backticks, $()) combined with
# command-like words. Never executes anything.

from __future__ import annotations

from engine.collectors.request_collector import multi_decode
from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult, Severity
from engine.detectors.base import BaseDetector
from engine.rules.signatures import COMMAND_SEPARATORS, COMMAND_WORDS


class CommandInjectionDetector(BaseDetector):
    name = 'CommandInjectionDetector'
    category = AttackCategory.COMMAND_INJECTION
    description = 'Flags shell metacharacters combined with command-like words.'

    def analyze(self, ctx: RequestContext) -> list[DetectionResult]:
        text = multi_decode(self._haystack(ctx))
        if not (COMMAND_SEPARATORS.search(text) and COMMAND_WORDS.search(text)):
            return []
        return [
            DetectionResult(
                detector_name=self.name,
                category=self.category,
                severity=Severity.CRITICAL,
                confidence=0.76,
                reason='Suspicious command-injection pattern (not executed)',
                evidence={'has_separator': True, 'has_command_word': True},
            )
        ]
