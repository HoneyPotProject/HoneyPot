# Defines RequestContext, a frozen dataclass with source IP, method, path,
# query params, headers, size-limited body, timestamp and request ID.
# Every detector receives only this object.

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping
import uuid


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class RequestContext:
    """
    Immutable view of one inbound HTTP request.

    Detectors must not receive raw sockets, files, or unredacted secrets.
    """

    source_ip: str
    method: str
    path: str
    query_params: Mapping[str, str]
    headers: Mapping[str, str]
    body: bytes
    timestamp: datetime = field(default_factory=_utc_now)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_port: int = 0
    raw_size: int = 0
    malformed: bool = False
