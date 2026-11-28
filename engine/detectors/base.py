"""Abstract base class for all honeypot security detectors."""

from abc import ABC, abstractmethod

from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult


class BaseDetector(ABC):
    """Interface that every security detector must implement.

    Subclasses must define ``name`` and ``category`` attributes and implement
    :meth:`analyze`.
    """

    name: str
    category: AttackCategory

    def __init__(self) -> None:
        self.enabled: bool = True
        self.detection_count: int = 0

    @abstractmethod
    def analyze(self, context: RequestContext) -> list[DetectionResult]:
        """Inspect a single immutable RequestContext.

        Returns zero or more DetectionResult objects. Detectors must never
        mutate the context or execute attacker-controlled input.
        """
