# Groups requests into sessions (IP plus time gap, and cookie if present)
# and tracks per-session activity.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import uuid


@dataclass
class SessionInfo:
    session_id: str
    request_count: int


class SessionAnalyzer:
    def __init__(self, gap_seconds: int = 300) -> None:
        self._gap = timedelta(seconds=gap_seconds)
        self._sessions: dict[str, tuple[datetime, str, int]] = {}

    def process(self, source_ip: str, timestamp: datetime, cookie: str) -> dict:
        now = timestamp or datetime.now(timezone.utc)
        cookie_key = ''
        if cookie and cookie != '[REDACTED]':
            cookie_key = hashlib.sha256(cookie.encode('utf-8')).hexdigest()[:12]
        key = f'{source_ip}:{cookie_key}'
        last = self._sessions.get(key)
        if last is None or now - last[0] > self._gap:
            session_id = str(uuid.uuid4())
            count = 1
        else:
            session_id = last[1]
            count = last[2] + 1
        self._sessions[key] = (now, session_id, count)
        return {'session_id': session_id, 'request_count': count}
