import pytest


@pytest.mark.asyncio
async def test_health_unauthenticated(client):
    response = await client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


@pytest.mark.asyncio
async def test_events_require_auth(client):
    response = await client.get('/api/events')
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_and_list_events(client):
    bad = await client.post('/api/auth/login', json={'username': 'admin', 'password': 'nope'})
    assert bad.status_code == 401
    ok = await client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin'})
    assert ok.status_code == 200
    events = await client.get('/api/events')
    assert events.status_code == 200
    body = events.json()
    assert 'events' in body
    assert 'total' in body


@pytest.mark.asyncio
async def test_statistics_and_detectors(client, api_headers):
    stats = await client.get('/api/statistics', headers=api_headers)
    assert stats.status_code == 200
    data = stats.json()
    assert 'total_events' in data
    assert 'critical_events' in data
    dets = await client.get('/api/detectors', headers=api_headers)
    assert dets.status_code == 200
    assert dets.json()['total'] >= 8


@pytest.mark.asyncio
async def test_system_status_checks_db(client, api_headers):
    status = await client.get('/api/system/status', headers=api_headers)
    assert status.status_code == 200
    body = status.json()
    assert body['database_status'] == 'ok'
    assert 'queue_depth' in body
    assert 'processed_events' in body
