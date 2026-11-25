from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SourceObservationOut(BaseModel):
    source_ip: str
    first_seen: datetime
    last_seen: datetime
    total_events: int
    last_category: Optional[str] = None
    category_counts: dict[str, int] = Field(default_factory=dict)
    severity_counts: dict[str, int] = Field(default_factory=dict)


class SourceListOut(BaseModel):
    sources: list[SourceObservationOut]
    total: int
    page: int
    page_size: int


class SourceEventOut(BaseModel):
    event_id: str
    timestamp: datetime
    attack_category: str
    severity: str
    path: str
    method: str


class TimelinePoint(BaseModel):
    time: str
    count: int
