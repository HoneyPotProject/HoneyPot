# Estimates automation likelihood from request timing, rate, and regularity.
# User-Agent is a weak hint only.

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

_BOT_HINTS = ('curl', 'wget', 'python-requests', 'scrapy', 'httpie', 'go-http-client')


class AutomationAnalyzer:
    def __init__(self, window_seconds: int = 30) -> None:
        self._window = timedelta(seconds=window_seconds)
        self._times: dict[str, deque[datetime]] = defaultdict(deque)

    def likelihood(self, source_ip: str, timestamp: datetime, user_agent: str) -> float:
        now = timestamp or datetime.now(timezone.utc)
        history = self._times[source_ip]
        history.append(now)
        while history and now - history[0] > self._window:
            history.popleft()

        rate = min(1.0, len(history) / 20.0)
        regularity = 0.0
        if len(history) >= 3:
            gaps = [
                (history[i] - history[i - 1]).total_seconds()
                for i in range(1, len(history))
            ]
            mean = sum(gaps) / len(gaps)
            if mean > 0:
                variance = sum((g - mean) ** 2 for g in gaps) / len(gaps)
                regularity = 0.4 if variance < 0.05 else 0.1

        ua = (user_agent or '').lower()
        ua_hint = 0.15 if any(h in ua for h in _BOT_HINTS) else 0.0
        return round(min(1.0, rate + regularity + ua_hint), 4)
