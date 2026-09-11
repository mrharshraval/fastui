import os
import sys
from collections.abc import AsyncGenerator

import pytest_asyncio

# Ensure services/api is on sys.path
root_services_api = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
root_services = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, root_services_api)
sys.path.insert(0, root_services)

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import app.infrastructure.database.session as db_session_module
from app.domains.models import Base, User, UserRole
from app.infrastructure.database.session import get_db
from app.main import app
from app.shared.security import create_access_token, get_password_hash

# Test In-Memory SQLite Database
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})

TestAsyncSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# Patch global session factories for background workers in tests
db_session_module.AsyncSessionLocal = TestAsyncSessionLocal
db_session_module.engine = test_engine


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def auth_client(client: AsyncClient, db_session: AsyncSession) -> AsyncClient:
    # Seed test user
    user = User(
        email="test@fastui.in",
        hashed_password=get_password_hash("password"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token({"user_id": user.id, "email": user.email, "role": "admin"})

    client.cookies.set("access_token", token)
    return client
