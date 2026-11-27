from abc import ABC, abstractmethod

from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult


class BaseDetector(ABC):
    description: str = ""
    version: str = "1.0"
    enabled: bool = True
    detection_count: int = 0

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique detector name, e.g. 'sql_injection'."""

    @property
    @abstractmethod
    def category(self) -> AttackCategory:
        """The attack category this detector reports."""

    @abstractmethod
    def analyze(self, context: RequestContext) -> list[DetectionResult]:
        """Return zero or more results. Must not modify context."""
