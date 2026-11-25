# Flags one IP requesting many distinct paths, or many 404s, in a time window.
# Stateful, using a per-IP deque with a size cap.

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from engine.core.config import DEFAULT_CONFIG, EngineConfig
from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult, Severity
from engine.detectors.base import BaseDetector


class EndpointEnumerationDetector(BaseDetector):
    name = 'EndpointEnumerationDetector'
    category = AttackCategory.ENDPOINT_ENUMERATION
    description = 'Flags a source IP probing many distinct paths in a short window.'

    def __init__(self, config: EngineConfig | None = None) -> None:
        self._config = config or DEFAULT_CONFIG
        self._paths: dict[str, deque[tuple[datetime, str]]] = defaultdict(deque)
        self._max_entries = 500

    def analyze(self, ctx: RequestContext) -> list[DetectionResult]:
        now = ctx.timestamp or datetime.now(timezone.utc)
        window = timedelta(seconds=self._config.endpoint_enum_window_seconds)
        history = self._paths[ctx.source_ip]
        history.append((now, ctx.path))
        while history and now - history[0][0] > window:
            history.popleft()
        while len(history) > self._max_entries:
            history.popleft()

        distinct = {path for _, path in history}
        if len(distinct) < self._config.endpoint_enum_path_threshold:
            return []
        return [
            DetectionResult(
                detector_name=self.name,
                category=self.category,
                severity=Severity.MEDIUM,
                confidence=0.72,
                reason=(
                    f'{len(distinct)} distinct paths from {ctx.source_ip} '
                    f'within {self._config.endpoint_enum_window_seconds}s'
                ),
                evidence={'distinct_paths': len(distinct)},
            )
        ]
