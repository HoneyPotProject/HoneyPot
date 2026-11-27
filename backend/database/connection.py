# SQLAlchemy engine and session factory.
# Uses aiosqlite for fully async database access.

import logging
import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.config import settings

logger = logging.getLogger(__name__)


# Base class for all ORM models.
class Base(DeclarativeBase):
    pass


# The async SQLAlchemy engine.
# echo=False in production; set to True to debug SQL queries.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={'check_same_thread': False},  # Required for SQLite.
)

# Session factory — each request gets its own session.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """
    FastAPI dependency that yields a database session.

    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """
    Create all tables if they do not exist.
    Called once at application startup.
    """
    # Ensure the data directory exists.
    db_path = settings.DATABASE_URL.replace('sqlite+aiosqlite:///', '')
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    # Import models so SQLAlchemy knows about them.
    from backend.database import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info('Database initialized.')
