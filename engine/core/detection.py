"""Shared enums and the DetectionResult model."""

from dataclasses import dataclass
from enum import Enum


# severity enum
class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# attack enum
class AttackCategory(str, Enum):
    DIRECTORY_ENUMERATION = "directory_enumeration"
    ENDPOINT_ENUMERATION = "endpoint_enumeration"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    BRUTE_FORCE = "brute_force"
    SUSPICIOUS_REQUEST = "suspicious_request"
    PORT_SCAN = "port_scan"


@dataclass(frozen=True)  # like static class now can not be change
class DetectionResult:
    detector: str
    category: AttackCategory
    severity: Severity
    confidence: float
    reason: str
    evidence: str

    def __post_init__(self) -> None:
        if not isinstance(self.confidence, (int, float)) or isinstance(self.confidence, bool):
            raise TypeError("confidence must be a number")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
