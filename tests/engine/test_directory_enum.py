import dataclasses

import pytest

from engine.core.detection import AttackCategory, Severity
from engine.detectors.directory_enum import DirectoryEnumerationDetector

detector = DirectoryEnumerationDetector()


def run(context, path):
    return detector.analyze(dataclasses.replace(context, path=path))


@pytest.mark.parametrize(
    "path",
    [
        "/.env",
        "/.git/config",
        "/phpmyadmin",
        "/backup.zip",
        "/ADMIN",
        "/%2eenv",
        "/.env?x=1",
        "/admin/",
    ],
)
def test_sensitive_paths_detected(context, path):
    assert len(run(context, path)) >= 1


def test_secret_paths_rank_higher_than_admin(context):
    env = run(context, "/.env")[0]
    admin = run(context, "/admin")[0]
    order = list(Severity)
    assert order.index(env.severity) > order.index(admin.severity)


def test_result_shape(context):
    result = run(context, "/.env")[0]
    assert result.category == AttackCategory.DIRECTORY_ENUMERATION
    assert 0.0 <= result.confidence <= 1.0
    assert "matched" in result.reason.lower()
    assert "succeeded" not in result.reason.lower()


def test_evidence_is_truncated(context):
    result = run(context, "/.git/" + "a" * 5000)[0]
    assert len(result.evidence) <= 200


def test_prefix_rule_does_not_match_lookalike(context):
    assert run(context, "/administrator-guide") == []
