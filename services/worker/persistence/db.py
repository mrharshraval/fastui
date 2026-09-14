import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool

from core.config import settings

logger = logging.getLogger("fastui.worker.db")

def _build_engine():
    db_url = settings.DATABASE_URL
    kwargs: Dict[str, Any] = {"echo": settings.DEBUG}

    if "sqlite" in db_url:
        if ":memory:" in db_url:
            kwargs["poolclass"] = StaticPool
            kwargs["connect_args"] = {"check_same_thread": False}
        else:
            kwargs["poolclass"] = NullPool
    else:
        kwargs.update({
            "pool_pre_ping": True,
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
            "connect_args": {
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
            },
        })

    return create_async_engine(db_url, **kwargs)

engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around a series of operations."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Session rollback because of exception: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def close_db_engine() -> None:
    """Disposes database engine pool during worker shutdown."""
    await engine.dispose()
    logger.info("Database engine pool disposed.")
