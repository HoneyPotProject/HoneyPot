# Converts an engine SecurityEvent into a plain dict the backend can store.

from engine.events.event import SecurityEvent


def to_db_dict(event: SecurityEvent) -> dict:
    """
    Map all SecurityEvent fields to a plain Python dict.

    This dict is what EventRepository.create() and EventService
    work with — it avoids passing engine objects into the database layer.
    """
    return {
        'event_id': str(event.event_id),
        'source_ip': event.source_ip,
        'timestamp': event.timestamp,
        'attack_category': (
            event.attack_category.value
            if hasattr(event.attack_category, 'value')
            else str(event.attack_category)
        ),
        'severity': (
            event.severity.value
            if hasattr(event.severity, 'value')
            else str(event.severity)
        ),
        'confidence': event.confidence,
        'detector_names': event.detector_names,
        'detection_reasons': event.detection_reasons,
        'evidence': event.evidence,
        'target': event.target,
        'method': event.method,
        'path': event.path,
        'request_id': event.request_id,
        'metadata': event.metadata,
    }
