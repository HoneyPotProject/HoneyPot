# Counts login attempts per IP in a sliding window against the fake login
# endpoint and flags when a threshold is crossed. Stateful.

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from engine.core.config import DEFAULT_CONFIG, EngineConfig
from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult, Severity
from engine.detectors.base import BaseDetector


class BruteForceDetector(BaseDetector):
    name = 'BruteForceDetector'
    category = AttackCategory.BRUTE_FORCE
    description = 'Flags repeated login attempts from one source IP.'

    def __init__(self, config: EngineConfig | None = None) -> None:
        self._config = config or DEFAULT_CONFIG
        self._attempts: dict[str, deque[datetime]] = defaultdict(deque)

    def analyze(self, ctx: RequestContext) -> list[DetectionResult]:
        path = (ctx.path or '').lower()
        if ctx.method not in {'POST', 'PUT'} and path not in self._config.login_paths:
            # Count POSTs to login paths, and also GET floods to login pages.
            if path not in {p.lower() for p in self._config.login_paths}:
                return []
            if ctx.method != 'POST':
                return []

        login_paths = {p.lower() for p in self._config.login_paths}
        if path not in login_paths:
            return []

        now = ctx.timestamp or datetime.now(timezone.utc)
        window = timedelta(seconds=self._config.brute_force_window_seconds)
        history = self._attempts[ctx.source_ip]
        history.append(now)
        while history and now - history[0] > window:
            history.popleft()

        if len(history) < self._config.brute_force_threshold:
            return []
        return [
            DetectionResult(
                detector_name=self.name,
                category=self.category,
                severity=Severity.HIGH,
                confidence=0.74,
                reason=(
                    f'{len(history)} login attempts from {ctx.source_ip} '
                    f'within {self._config.brute_force_window_seconds}s'
                ),
                evidence={'attempt_count': len(history), 'path': ctx.path},
            )
        ]
