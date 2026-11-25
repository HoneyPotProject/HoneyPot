import asyncio
from types import MappingProxyType
from datetime import datetime, timezone

from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult, Severity
from engine.events.event import SecurityEvent
from engine.events.event_processor import EventProcessor
from engine.events.storage_interface import EventSink


class MemorySink(EventSink):
    def __init__(self):
        self.events: list[SecurityEvent] = []

    async def save(self, event: SecurityEvent) -> None:
        self.events.append(event)


def test_processor_merges_and_saves():
    sink = MemorySink()
    processor = EventProcessor(sink)
    ctx = RequestContext(
        source_ip='10.0.0.8',
        method='GET',
        path='/x',
        query_params=MappingProxyType({}),
        headers=MappingProxyType({}),
        body=b'',
        timestamp=datetime.now(timezone.utc),
        request_id='req-1',
    )
    results = [
        DetectionResult('A', AttackCategory.XSS, Severity.LOW, 0.4, 'low', {}),
        DetectionResult('B', AttackCategory.SQL_INJECTION, Severity.HIGH, 0.9, 'high', {'q': '1'}),
    ]
    event = asyncio.get_event_loop().run_until_complete(processor.process(ctx, results))
    assert event is not None
    assert event.severity == Severity.HIGH
    assert event.attack_category == AttackCategory.SQL_INJECTION
    assert sink.events


def test_processor_skips_empty_results():
    sink = MemorySink()
    processor = EventProcessor(sink)
    ctx = RequestContext(
        source_ip='10.0.0.8',
        method='GET',
        path='/',
        query_params=MappingProxyType({}),
        headers=MappingProxyType({}),
        body=b'',
        timestamp=datetime.now(timezone.utc),
        request_id='req-2',
    )
    event = asyncio.get_event_loop().run_until_complete(processor.process(ctx, []))
    assert event is None
    assert sink.events == []
