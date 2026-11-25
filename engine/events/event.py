# Defines SecurityEvent: event ID, IP, timestamp, category, severity,
# confidence, reasons, evidence, target, method, path, related results.

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from engine.core.detection import AttackCategory, DetectionResult, Severity


@dataclass
class SecurityEvent:
    """Normalized incident produced by EventProcessor. Engine source of truth."""

    event_id: uuid.UUID
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
    detector_names: list[str]
    related_results: list[DetectionResult] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
