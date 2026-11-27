"""SecurityEvent: the consolidated event produced by the event processor."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from engine.core.detection import AttackCategory, DetectionResult, Severity


@dataclass
class SecurityEvent:
    event_id: str
    source_ip: str
    timestamp: datetime
    attack_category: AttackCategory
    severity: Severity
    confidence: float
    detection_reasons: list[str]
    evidence: dict[str, Any]
    target: str
    method: str
    path: str
    request_id: str
    detector_names: list[str] = field(default_factory=list)
    related_results: list[DetectionResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
