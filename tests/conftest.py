from __future__ import annotations

import os
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault('API_KEY', 'test-api-key')
os.environ.setdefault('ADMIN_USERNAME', 'admin')
os.environ.setdefault('ADMIN_PASSWORD', 'adminHoneyPot1')
os.environ.setdefault('SESSION_SECRET', 'test-session-secret')
os.environ.setdefault('HONEYPOT_HOST', '127.0.0.1')
os.environ['HONEYPOT_PORT'] = os.environ.get('TEST_HONEYPOT_PORT', '18080')
os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///' + str(ROOT / 'data' / 'database' / 'test_honeypot.db')
os.environ['ENABLE_DECOY_PORTS'] = 'false'

from backend.config import settings  # noqa: E402

settings.API_KEY = 'test-api-key'
settings.ADMIN_USERNAME = 'admin'
settings.ADMIN_PASSWORD = 'adminHoneyPot1'
settings.HONEYPOT_PORT = int(os.environ['HONEYPOT_PORT'])
settings.HONEYPOT_HOST = '127.0.0.1'
settings.ENABLE_DECOY_PORTS = False
settings.DATABASE_URL = os.environ['DATABASE_URL']


@pytest.fixture
def api_headers() -> dict[str, str]:
    return {'X-API-Key': 'test-api-key'}


@pytest.fixture
async def client():
    from backend.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as ac:
        yield ac
