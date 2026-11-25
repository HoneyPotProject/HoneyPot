# Correlates events per source IP over time: repeated categories, multiple
# attack types, sequential scanning. Produces a behavioral score.

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone

from engine.core.detection import AttackCategory


class BehaviorAnalyzer:
    """Lightweight per-IP category history. Does not classify attacks."""

    def __init__(self, max_history: int = 50) -> None:
        self._history: dict[str, deque[AttackCategory]] = defaultdict(
            lambda: deque(maxlen=max_history)
        )

    def score(self, source_ip: str, category: AttackCategory) -> float:
        history = self._history[source_ip]
        history.append(category)
        unique = set(history)
        repeat = history.count(category) / max(1, len(history))
        diversity = min(1.0, len(unique) / 5.0)
        return round(min(1.0, 0.5 * repeat + 0.5 * diversity), 4)
