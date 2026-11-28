"""Signature lists, grouped by category. Tune rules here, not inside detectors."""

from dataclasses import dataclass
from typing import Literal

from engine.core.detection import Severity


@dataclass(frozen=True)
class PathRule:
    pattern: str  # lowercase, starts with "/"
    match: Literal["exact", "prefix"]  # a Literal type allows only these two strings
    severity: Severity
    confidence: float
    description: str


# Starting values. They are tunable guesses, not verified facts.
# "prefix" is segment-aware: "/admin" matches "/admin" and "/admin/x" but NOT "/administrator-guide".
PATH_RULES: tuple[PathRule, ...] = (
    PathRule("/.env", "exact", Severity.HIGH, 0.9, "environment file"),
    PathRule("/.git", "prefix", Severity.HIGH, 0.9, "git repository data"),
    PathRule("/backup.zip", "exact", Severity.MEDIUM, 0.8, "backup archive"),
    PathRule("/phpmyadmin", "prefix", Severity.MEDIUM, 0.6, "database admin panel"),
    PathRule("/admin", "prefix", Severity.LOW, 0.5, "admin page"),
    PathRule("/wp-admin", "prefix", Severity.LOW, 0.5, "WordPress admin"),
    PathRule("/wp-login.php", "exact", Severity.LOW, 0.5, "WordPress login"),
)