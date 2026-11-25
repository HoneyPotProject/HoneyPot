from pydantic import BaseModel, Field


class StatisticsOut(BaseModel):
    total_events: int
    unique_sources: int
    critical_events: int
    high_severity_events: int
    events_last_24h: int
    enabled_detectors: int
    category_distribution: dict[str, int] = Field(default_factory=dict)
    severity_distribution: dict[str, int] = Field(default_factory=dict)


class DetectorOut(BaseModel):
    name: str
    category: str
    description: str = ''
    enabled: bool = True
    detection_count: int = 0
    version: str = '1.0'


class SystemStatusOut(BaseModel):
    backend_status: str
    engine_running: bool
    database_status: str
    queue_depth: int
    queue_capacity: int
    processed_events: int
    dropped_events: int
    processing_errors: int
    last_processed_event: str | None = None
    ws_connections: int
    uptime_seconds: float
    honeypot_port: int
