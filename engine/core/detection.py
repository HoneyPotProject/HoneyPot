# Defines DetectionResult (detector name, category, severity, confidence,
# reason, evidence) plus Severity and AttackCategory enums.

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """How dangerous is this event? Used for triage and dashboard colouring."""
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'


class AttackCategory(str, Enum):
    """Broad category of the attack pattern detected."""
    SQL_INJECTION = 'sql_injection'
    XSS = 'xss'
    PATH_TRAVERSAL = 'path_traversal'
    COMMAND_INJECTION = 'command_injection'
    DIRECTORY_ENUMERATION = 'directory_enumeration'
    ENDPOINT_ENUMERATION = 'endpoint_enumeration'
    BRUTE_FORCE = 'brute_force'
    SUSPICIOUS_REQUEST = 'suspicious_request'
    PORT_SCAN = 'port_scan'
    UNKNOWN = 'unknown'


# Ordering used when merging multiple results: higher index = higher priority.
SEVERITY_ORDER = [
    Severity.LOW,
    Severity.MEDIUM,
    Severity.HIGH,
    Severity.CRITICAL,
]


@dataclass
class DetectionResult:
    """
    What one detector found after examining a RequestContext.

    The EventProcessor merges all results from all detectors
    into a single SecurityEvent.
    """

    detector_name: str           # e.g. 'SQLInjectionDetector'
    category: AttackCategory
    severity: Severity
    confidence: float            # 0.0 (low) to 1.0 (certain)
    reason: str                  # Human-readable explanation
    evidence: dict = field(default_factory=dict)   # Raw matched values, never executed