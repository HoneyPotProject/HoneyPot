import asyncio
from datetime import datetime, timezone
import uuid

from backend.integration.event_sink import BackendEventSink
from engine.core.detection import AttackCategory, Severity
from engine.events.event import SecurityEvent


def _event() -> SecurityEvent:
    return SecurityEvent(
        event_id=uuid.uuid4(),
        source_ip='1.2.3.4',
        timestamp=datetime.now(timezone.utc),
        attack_category=AttackCategory.XSS,
        severity=Severity.LOW,
        confidence=0.4,
        detection_reasons=['t'],
        evidence={},
        target='/',
        method='GET',
        path='/',
        request_id='r',
        detector_names=['XSSDetector'],
    )


async def test_queue_overflow_drops_without_raising():
    queue: asyncio.Queue = asyncio.Queue(maxsize=1)
    dropped = [0]
    sink = BackendEventSink(queue, dropped)
    await sink.save(_event())
    await sink.save(_event())
    assert dropped[0] == 1
    assert queue.qsize() == 1
