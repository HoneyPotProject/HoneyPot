from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SecurityEventOut(BaseModel):
    event_id: str
    source_ip: str
    timestamp: datetime
    attack_category: str
    severity: str
    confidence: float
    detector_names: list[str] = Field(default_factory=list)
    detection_reasons: list[str] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)
    target: str
    method: str
    path: str
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class EventListOut(BaseModel):
    events: list[SecurityEventOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class AnnotationIn(BaseModel):
    status: str = 'new'
    notes: str | None = None
    analyst_id: str = 'analyst'


class AnnotationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: str
    analyst_id: str
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
