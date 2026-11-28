import pytest

from engine.core.engine import DetectionEngine


def test_dummy_detector_runs_through_engine(context, dummy):
    engine = DetectionEngine()
    engine.register_detector(dummy)
    results = engine.analyze(context)
    assert len(results) == 1
    assert results[0].detector == "dummy"


def test_failing_detector_does_not_stop_others(context, dummy, broken):
    engine = DetectionEngine()
    engine.register_detector(broken)
    engine.register_detector(dummy)
    assert len(engine.analyze(context)) == 1


def test_duplicate_name_rejected(dummy):
    engine = DetectionEngine()
    engine.register_detector(dummy)
    with pytest.raises(ValueError):
        engine.register_detector(dummy)


def test_non_detector_rejected():
    with pytest.raises(TypeError):
        DetectionEngine().register_detector(object())


def test_disabled_detector_skipped(context, dummy):
    dummy.enabled = False
    engine = DetectionEngine()
    engine.register_detector(dummy)
    assert engine.analyze(context) == []


def test_detection_count_increments(context, dummy):
    engine = DetectionEngine()
    engine.register_detector(dummy)
    engine.analyze(context)
    engine.analyze(context)
    assert dummy.detection_count == 2