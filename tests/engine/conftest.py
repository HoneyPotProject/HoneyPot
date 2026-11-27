from datetime import UTC, datetime

import pytest

from engine.core.context import RequestContext
from engine.core.detection import AttackCategory, DetectionResult, Severity
from engine.detectors.base import BaseDetector


@pytest.fixture
def context() -> RequestContext:
    return RequestContext(
        source_ip="127.0.0.1",
        method="GET",
        path="/",
        query_params={},
        headers={"host": "localhost"},
        body="",
        timestamp=datetime.now(UTC),
        request_id="req-1",
    )


class DummyDetector(BaseDetector):
    name = "dummy"
    category = AttackCategory.SUSPICIOUS_REQUEST

    def analyze(self, context):
        return [DetectionResult("dummy", self.category, Severity.LOW, 0.5, "test", "x")]


class BrokenDetector(BaseDetector):
    name = "broken"
    category = AttackCategory.XSS

    def analyze(self, context):
        raise RuntimeError("boom")


@pytest.fixture
def dummy():
    return DummyDetector()


@pytest.fixture
def broken():
    return BrokenDetector()
