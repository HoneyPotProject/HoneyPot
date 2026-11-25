# Flags one IP hitting many different decoy ports within a window.

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from engine.core.config import DEFAULT_CONFIG, EngineConfig
from engine.core.detection import AttackCategory, DetectionResult, Severity


class PortScanDetector:
    name = 'PortScanDetector'
    category = AttackCategory.PORT_SCAN
    description = 'Flags one source IP connecting to many decoy TCP ports.'
    enabled = True
    detection_count = 0
    version = '1.0'

    def __init__(self, config: EngineConfig | None = None) -> None:
        self._config = config or DEFAULT_CONFIG
        self._hits: dict[str, deque[tuple[datetime, int]]] = defaultdict(deque)

    def record(self, source_ip: str, port: int, timestamp: datetime | None = None) -> DetectionResult | None:
        now = timestamp or datetime.now(timezone.utc)
        window = timedelta(seconds=self._config.port_scan_window_seconds)
        history = self._hits[source_ip]
        history.append((now, port))
        while history and now - history[0][0] > window:
            history.popleft()
        ports = {p for _, p in history}
        if len(ports) < self._config.port_scan_port_threshold:
            return None
        self.detection_count += 1
        return DetectionResult(
            detector_name=self.name,
            category=self.category,
            severity=Severity.MEDIUM,
            confidence=0.7,
            reason=f'Source {source_ip} connected to {len(ports)} decoy ports',
            evidence={'ports': sorted(ports)},
        )
