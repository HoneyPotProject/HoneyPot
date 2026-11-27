# Administrator authentication: API key, session cookie.
# Password hashing lives in backend/passwords.py.

from __future__ import annotations

import hashlib
import hmac
import logging
import time

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from backend.config import settings
from backend.passwords import hash_password, verify_password  # re-exported for other modules

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)
COOKIE_NAME = 'hp_session'

_ADMIN_PASSWORD_HASH = hash_password(settings.ADMIN_PASSWORD)


def _safe_equals(a: str, b: str) -> bool:
    """Constant-time comparison that cannot crash on non-ASCII input."""
    return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


def _sign(payload: str) -> str:
    return hmac.new(
        settings.SESSION_SECRET.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


def create_session_token(username: str) -> str:
    expiry = int(time.time()) + settings.SESSION_TTL_SECONDS
    payload = f'{username}|{expiry}'
    return f'{payload}|{_sign(payload)}'


def parse_session_token(token: str | None) -> str | None:
    if not token:
        return None
    parts = token.split('|')
    if len(parts) != 3:
        return None
    username, expiry_s, signature = parts
    if not _safe_equals(signature, _sign(f'{username}|{expiry_s}')):
        return None
    try:
        expiry = int(expiry_s)
    except ValueError:
        return None
    if expiry < time.time():
        return None
    return username


def authenticate_credentials(username: str, password: str) -> bool:
    user_ok = _safe_equals(username, settings.ADMIN_USERNAME)
    pass_ok = verify_password(password, _ADMIN_PASSWORD_HASH)  # always runs
    return user_ok and pass_ok


async def require_auth(
    request: Request,
    api_key: str | None = Security(api_key_header),
) -> str:
    if api_key:
        if _safe_equals(api_key, settings.API_KEY):
            return 'api-key'
        logger.warning('Invalid API key attempt from %s', request.client.host if request.client else '?')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid API key')

    username = parse_session_token(request.cookies.get(COOKIE_NAME))
    if username:
        return username

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required')


def authenticate_websocket(api_key: str | None, cookie_header: str | None) -> bool:
    if api_key and _safe_equals(api_key, settings.API_KEY):
        return True
    if not cookie_header:
        return False
    for part in cookie_header.split(';'):
        name, _, value = part.strip().partition('=')
        if name == COOKIE_NAME:
            return parse_session_token(value) is not None
    return False