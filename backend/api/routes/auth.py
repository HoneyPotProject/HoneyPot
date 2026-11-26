
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

EMAIL_PATTERN = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
from backend.api.dependencies import get_db, require_auth
from backend.auth import (
    COOKIE_NAME,
    authenticate_credentials,
    create_session_token,
)
from backend.config import settings
from backend.database.repository import (
    SourceRepository,
    UserRepository,
)
from backend.passwords import hash_password, verify_password


router = APIRouter()


class SignupIn(BaseModel):
    username: str = Field(min_length=2, max_length=100, pattern=r'^[A-Za-z0-9_.\- ]+$')
    email: str = Field(min_length=5, max_length=100, pattern=EMAIL_PATTERN)
    password: str = Field(min_length=12, max_length=200)


class LoginIn(BaseModel):
    email: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


def set_session_cookie(response: Response, username: str):
    """Create and attach an authenticated session cookie."""

    token = create_session_token(username)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite='lax',
        secure=False,
        max_age=settings.SESSION_TTL_SECONDS,
        path='/',
    )


@router.post('/api/auth/signup', tags=['Auth'])
async def signup(
    payload: SignupIn,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Register the initial dashboard administrator.

    Public registration is disabled after the first account.
    """

    #Check whether an administrator already exists.
    user_count = await UserRepository.count_users(db)

    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Registration is disabled. An administrator already exists.',
        )

    password_hash = hash_password(payload.password)

    try:
        user = await UserRepository.create(
            session=db,
            username=payload.username.strip(),
            email=payload.email.strip().lower(),
            password_hash=password_hash,
        )

        await db.flush()

    except Exception:
        # Let get_db() roll back the transaction.
        raise

    # Record successful registration.
    await SourceRepository.write_audit(
        db,
        actor=user.username,
        action='signup_success',
        source_ip=request.client.host if request.client else None,
    )

    # Automatically log in after registration.
    set_session_cookie(response, user.username)

    return {
        'status': 'ok',
        'message': 'Administrator account created successfully.',
        'username': user.username,
        'role': user.role,
    }


@router.post('/api/auth/login', tags=['Auth'])
async def login(
    payload: LoginIn,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await UserRepository.get_by_email(
        db,
        payload.email.strip().lower(),
    )

    authenticated = False

    if user is not None:
        authenticated = verify_password(
            payload.password,
            user.password_hash,
        )
    else:
        # Preserve configured administrator credentials.
        authenticated = authenticate_credentials(
            payload.email,
            payload.password,
        )

    if not authenticated:
        await SourceRepository.write_audit(
            db,
            actor=payload.email,
            action='login_failed',
            source_ip=request.client.host if request.client else None,
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid credentials',
        )

    # Use the authenticated database account's username.
    username = user.username if user is not None else settings.ADMIN_USERNAME

    set_session_cookie(response, username)

    await SourceRepository.write_audit(
        db,
        actor=username,
        action='login_success',
        source_ip=request.client.host if request.client else None,
    )

    return {
        'status': 'ok',
        'username': username,
    }

@router.post('/api/auth/logout', tags=['Auth'])
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: str = Depends(require_auth),
):
    response.delete_cookie(
        key=COOKIE_NAME,
        path='/',
    )

    await SourceRepository.write_audit(
        db,
        actor=user,
        action='logout',
        source_ip=request.client.host if request.client else None,
    )

    return {'status': 'ok'}


@router.get('/api/auth/me', tags=['Auth'])
async def me(
    user: str = Depends(require_auth),
    db: AsyncSession = Depends(get_db),
):
    account = await UserRepository.get_by_email(db, user)

    return {
        'username': user,
        'role': account.role if account else 'administrator',
    }
