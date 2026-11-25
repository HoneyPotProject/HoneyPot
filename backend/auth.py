# Administrator authentication: API key, session cookie, password hashing.

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
from typing import Optional

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from backend.config import settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name='X-API-Key', auto_error=False)
COOKIE_NAME = 'hp_session'
PBKDF2_ITERATIONS = 200_000


def hash_password(password: str, salt: str | None = None) -> str:
    salt_bytes = (salt or secrets.token_hex(16)).encode('utf-8')
    if salt:
        salt_bytes = salt.encode('utf-8')
    else:
        salt = secrets.token_hex(16)
        salt_bytes = salt.encode('utf-8')
    digest = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_bytes,
        PBKDF2_ITERATIONS,
    )
    return f'{salt}${digest.hex()}'


def verify_password(password: str, stored: str) -> bool:
    if '$' not in stored:
        return hmac.compare_digest(password, stored)
    salt, _digest = stored.split('$', 1)
    return hmac.compare_digest(hash_password(password, salt), stored)


_ADMIN_PASSWORD_HASH = hash_password(settings.ADMIN_PASSWORD)


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


def parse_session_token(token: str | None) -> Optional[str]:
    if not token:
        return None
    parts = token.split('|')
    if len(parts) != 3:
        return None
    username, expiry_s, signature = parts
    payload = f'{username}|{expiry_s}'
    expected = _sign(payload)
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        expiry = int(expiry_s)
    except ValueError:
        return None
    if expiry < time.time():
        return None
    return username


def authenticate_credentials(username: str, password: str) -> bool:
    if not hmac.compare_digest(username, settings.ADMIN_USERNAME):
        return False
    return verify_password(password, _ADMIN_PASSWORD_HASH)


async def require_auth(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
) -> str:
    if api_key:
        if hmac.compare_digest(api_key, settings.API_KEY):
            return 'api-key'
        logger.warning('Invalid API key attempt from %s', request.client.host if request.client else '?')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid API key',
        )

    username = parse_session_token(request.cookies.get(COOKIE_NAME))
    if username:
        return username

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Authentication required',
    )


def authenticate_websocket(api_key: str | None, cookie_header: str | None) -> bool:
    if api_key and hmac.compare_digest(api_key, settings.API_KEY):
        return True
    if not cookie_header:
        return False
    for part in cookie_header.split(';'):
        name, _, value = part.strip().partition('=')
        if name == COOKIE_NAME:
            return parse_session_token(value) is not None
    return False
