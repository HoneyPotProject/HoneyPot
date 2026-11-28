import pytest

from engine.core.detection import AttackCategory, DetectionResult, Severity


def test_severity_values():
    assert [s.value for s in Severity] == ["info", "low", "medium", "high", "critical"]


def test_category_values():
    assert len(AttackCategory) == 9
    assert AttackCategory.SQL_INJECTION.value == "sql_injection"


@pytest.mark.parametrize("bad", [-0.1, 1.1])
def test_confidence_out_of_range_rejected(bad):
    with pytest.raises(ValueError):
        DetectionResult("d", AttackCategory.XSS, Severity.LOW, bad, "r", "e")
