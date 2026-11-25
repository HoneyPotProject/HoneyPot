import asyncio
import socket

import pytest


def _send(port: int, payload: bytes) -> None:
    with socket.create_connection(('127.0.0.1', port), timeout=3) as sock:
        sock.sendall(payload)
        sock.settimeout(2)
        try:
            sock.recv(2048)
        except OSError:
            pass


@pytest.mark.asyncio
async def test_http_probe_persists_and_is_queryable(client, api_headers):
    from backend.config import settings

    _send(
        settings.HONEYPOT_PORT,
        b"GET /search?q=1'+UNION+SELECT+password+FROM+users HTTP/1.1\r\nHost: localhost\r\n\r\n",
    )
    found = None
    for _ in range(20):
        await asyncio.sleep(0.15)
        response = await client.get('/api/events', headers=api_headers)
        assert response.status_code == 200
        payload = response.json()
        if payload['total'] > 0:
            found = payload['events'][0]
            break
    assert found is not None, 'engine event was not persisted'
    assert found['source_ip']
    assert found['attack_category']
    detail = await client.get(f"/api/events/{found['event_id']}", headers=api_headers)
    assert detail.status_code == 200
    stats = await client.get('/api/statistics', headers=api_headers)
    assert stats.json()['total_events'] >= 1
