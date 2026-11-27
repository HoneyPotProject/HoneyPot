# ORM tables: security_events, source_observations, analyst_annotations, audit_log.

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database.connection import Base


def _now():
    return datetime.now(UTC)

class UserModel(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True, index=True)
    email=Column(String(100), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default='administrator')
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_now,
    )
class SecurityEventModel(Base):
    """
    One row per security event detected by the honeypot engine.

    JSON fields (stored as Text) hold variable-length data like
    lists of reasons and evidence dictionaries.
    """
    __tablename__ = 'security_events'

    # Internal auto-increment primary key.
    id = Column(Integer, primary_key=True, autoincrement=True)

    # UUID from the engine (string form for SQLite compatibility).
    event_id = Column(String(36), unique=True, nullable=False, index=True,default=lambda: str(uuid.uuid4()))

    # Where the attack came from.
    source_ip = Column(String(45), nullable=False, index=True)

    # When it happened.
    timestamp = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)

    # Attack classification.
    attack_category = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    confidence = Column(Float, nullable=False, default=0.0)

    # Which detectors fired (JSON array stored as text).
    detector_names = Column(Text, nullable=False, default='[]')

    # Human-readable explanations (JSON array stored as text).
    detection_reasons = Column(Text, nullable=False, default='[]')

    # Raw evidence (JSON object stored as text).
    evidence = Column(Text, nullable=False, default='{}')

    # What was targeted.
    target = Column(String(500), nullable=False, default='/')

    # HTTP method.
    method = Column(String(20), nullable=False, default='GET')

    # Request path.
    path = Column(String(500), nullable=False, default='/')

    # Correlates back to the engine request.
    request_id = Column(String(36), nullable=True)

    # Arbitrary extra metadata (session info, behavioral scores, etc.).
    metadata_json = Column(Text, nullable=False, default='{}')

    # Relationship to analyst annotations.
    annotations = relationship('AnalystAnnotationModel', back_populates='event',cascade='all, delete-orphan')

    __table_args__ = (
        # Composite index for the most common dashboard query.
        Index('ix_events_ip_timestamp', 'source_ip', 'timestamp'),
    )


class SourceObservationModel(Base):
    """
    Aggregated stats per source IP.

    Updated (upserted) every time a new event arrives from that IP.
    """
    __tablename__ = 'source_observations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_ip = Column(String(45), unique=True, nullable=False, index=True)
    first_seen = Column(DateTime(timezone=True), nullable=False, default=_now)
    last_seen = Column(DateTime(timezone=True), nullable=False, default=_now)
    total_events = Column(Integer, nullable=False, default=0)
    # Last seen attack category.
    last_category = Column(String(50), nullable=True)
    # JSON: {category: count} map.
    category_counts = Column(Text, nullable=False, default='{}')
    # JSON: {severity: count} map.
    severity_counts = Column(Text, nullable=False, default='{}')


class AnalystAnnotationModel(Base):
    """
    Analyst notes attached to a security event.

    Status values: new | under_review | reviewed | false_positive
    """
    __tablename__ = 'analyst_annotations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(36), ForeignKey('security_events.event_id'),nullable=False, index=True)
    analyst_id = Column(String(100), nullable=False, default='system')
    status = Column(String(30), nullable=False, default='new')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)

    event = relationship('SecurityEventModel', back_populates='annotations')


class AuditLogModel(Base):
    """
    Log of administrative actions (login, config changes, exports, etc.).
    """
    __tablename__ = 'audit_log'

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=_now, index=True)
    actor = Column(String(100), nullable=False, default='system')
    action = Column(String(100), nullable=False)
    detail = Column(Text, nullable=True)
    source_ip = Column(String(45), nullable=True)
