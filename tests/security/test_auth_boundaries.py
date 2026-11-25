import pytest


@pytest.mark.asyncio
async def test_management_routes_not_public(client):
    for path in (
        '/api/events',
        '/api/attackers',
        '/api/statistics',
        '/api/detectors',
        '/api/system/status',
    ):
        response = await client.get(path)
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_is_public(client):
    response = await client.get('/api/health')
    assert response.status_code == 200
