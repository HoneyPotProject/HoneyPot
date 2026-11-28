import dataclasses

import pytest

from engine.core.config import EngineConfig


def test_defaults_are_positive():
    cfg = EngineConfig()
    assert cfg.max_tracked_sources == 10_000
    assert cfg.brute_force_attempts == 5


def test_config_is_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        EngineConfig().max_body_bytes = 1


def test_invalid_value_rejected():
    with pytest.raises(ValueError):
        EngineConfig(max_connections=0)