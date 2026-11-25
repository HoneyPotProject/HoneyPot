from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db, require_auth
from backend.auth import COOKIE_NAME, authenticate_credentials, create_session_token
from backend.config import settings
from backend.database.repository import SourceRepository

router = APIRouter()


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


@router.post('/api/auth/login', tags=['Auth'])
async def login(
    payload: LoginIn,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    if not authenticate_credentials(payload.username, payload.password):
        await SourceRepository.write_audit(
            db,
            actor=payload.username,
            action='login_failed',
            source_ip=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

    token = create_session_token(payload.username)
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite='lax',
        secure=False,
        max_age=settings.SESSION_TTL_SECONDS,
        path='/',
    )
    await SourceRepository.write_audit(
        db,
        actor=payload.username,
        action='login_success',
        source_ip=request.client.host if request.client else None,
    )
    return {'status': 'ok', 'username': payload.username}


@router.post('/api/auth/logout', tags=['Auth'])
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(require_auth),
):
    response.delete_cookie(COOKIE_NAME, path='/')
    await SourceRepository.write_audit(
        db,
        actor=user,
        action='logout',
        source_ip=request.client.host if request.client else None,
    )
    return {'status': 'ok'}


@router.get('/api/auth/me', tags=['Auth'])
async def me(user: str = Depends(require_auth)):
    return {'username': user, 'role': 'administrator'}
