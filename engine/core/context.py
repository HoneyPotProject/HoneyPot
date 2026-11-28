from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType


@dataclass(frozen=True)
class RequestContext:
    source_ip: str
    method: str
    path: str
    query_params: Mapping[str, str]
    headers: Mapping[str, str]
    body: str
    timestamp: datetime
    request_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "query_params", MappingProxyType(dict(self.query_params)))
        object.__setattr__(self, "headers", MappingProxyType(dict(self.headers)))
