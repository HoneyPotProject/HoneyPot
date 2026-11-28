import pytest

from engine.detectors.base import BaseDetector


def test_base_detector_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseDetector()


def test_subclass_missing_analyze_cannot_be_instantiated():
    class Incomplete(BaseDetector):
        name = "x"
        category = None

    with pytest.raises(TypeError):
        Incomplete()
