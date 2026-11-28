import dataclasses

import pytest

from engine.core.engine import DetectionEngine
from engine.detectors.directory_enum import DirectoryEnumerationDetector

LEGIT_PATHS = [
    "/", "/index.html", "/search", "/blog/intro-to-sql", "/static/app.js",
    "/login", "/about", "/files/report..v2.pdf",
]


@pytest.mark.parametrize("path", LEGIT_PATHS)
def test_legit_paths_produce_no_detections(context, path):
    engine = DetectionEngine()
    engine.register_detector(DirectoryEnumerationDetector())
    assert engine.analyze(dataclasses.replace(context, path=path)) == []