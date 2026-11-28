import dataclasses

import pytest


def test_context_is_immutable(context):
    with pytest.raises(dataclasses.FrozenInstanceError):
        context.path = "/hacked"


def test_context_has_all_agreed_fields(context):
    names = {f.name for f in dataclasses.fields(context)}
    assert names == {
        "source_ip",
        "method",
        "path",
        "query_params",
        "headers",
        "body",
        "timestamp",
        "request_id",
    }