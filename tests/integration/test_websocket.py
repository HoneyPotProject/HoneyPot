import pytest
from starlette.testclient import TestClient


def test_websocket_rejects_bad_key_and_accepts_api_key():
    from backend.main import app

    with TestClient(app) as client:
        with pytest.raises(Exception), client.websocket_connect('/ws/events?api_key=wrong'):
            pass
        with client.websocket_connect('/ws/events?api_key=test-api-key') as ws:
            ws.send_text('ping')
