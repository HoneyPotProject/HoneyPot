import dataclasses

from engine.events.event import SecurityEvent

EXPECTED = {
    "event_id", "source_ip", "timestamp", "attack_category", "severity",
    "confidence", "detection_reasons", "evidence", "target", "method",
    "path", "request_id", "detector_names", "related_results", "metadata",
}


def test_event_has_agreed_fields():
    assert EXPECTED <= {f.name for f in dataclasses.fields(SecurityEvent)}


def test_default_lists_are_not_shared():
    fields = {f.name: f for f in dataclasses.fields(SecurityEvent)}
    assert fields["related_results"].default_factory is list
    assert fields["detector_names"].default_factory is list