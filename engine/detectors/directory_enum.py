"""Flags requests to sensitive or commonly scanned paths. Stateless, no I/O."""

from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult
from engine.core.normalizer import normalize
from engine.detectors.base import BaseDetector
from engine.rules.signatures import PATH_RULES, PathRule


def _matches(rule: PathRule, path: str) -> bool:
    if rule.match == "exact":
        return path == rule.pattern
    return path == rule.pattern or path.startswith(rule.pattern + "/")


class DirectoryEnumerationDetector(BaseDetector):
    name = "directory_enumeration"
    category = AttackCategory.DIRECTORY_ENUMERATION
    description = "Flags requests to sensitive or commonly scanned paths"

    def analyze(self, context: RequestContext) -> list[DetectionResult]:
        path = normalize(context.path.split("?", 1)[0])
        if len(path) > 1:
            path = path.rstrip("/")  # "/admin/" -> "/admin", but "/" stays "/"

        return [
            DetectionResult(
                detector=self.name,
                category=self.category,
                severity=rule.severity,
                confidence=rule.confidence,
                reason=f"Request matched a sensitive path pattern ({rule.description})",
                evidence=path[:200],
            )
            for rule in PATH_RULES
            if _matches(rule, path)
        ]
