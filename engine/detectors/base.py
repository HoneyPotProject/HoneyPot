# Abstract BaseDetector with name, category and analyze(ctx) -> list[DetectionResult].
# All detectors inherit it, so adding a new one means adding a file and registering it.

from __future__ import annotations

from abc import ABC, abstractmethod

from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult


class BaseDetector(ABC):
    """Contract for every detector registered with DetectionEngine."""

    name: str = 'BaseDetector'
    category: AttackCategory = AttackCategory.UNKNOWN
    description: str = ''
    version: str = '1.0'
    enabled: bool = True
    detection_count: int = 0

    @abstractmethod
    def analyze(self, ctx: RequestContext) -> list[DetectionResult]:
        """Inspect a request. Return an empty list when nothing suspicious is found."""
        raise NotImplementedError

    def _haystack(self, ctx: RequestContext) -> str:
        parts = [ctx.path, ctx.method]
        parts.extend(f'{k}={v}' for k, v in ctx.query_params.items())
        try:
            parts.append(ctx.body.decode('utf-8', errors='replace'))
        except Exception:
            pass
        return ' '.join(parts)
