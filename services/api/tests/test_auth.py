import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.schema import User, UserRole
from services.auth_service import get_password_hash, verify_password

def test_password_hashing():
    pw = "secret123"
    hashed = get_password_hash(pw)
    assert verify_password(pw, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client: AsyncClient):
    res = await client.get("/businesses", headers={"Authorization": "Bearer invalid_token_12345"})
    assert res.status_code == 401
    assert "detail" in res.json() or "error" in res.json()

@pytest.mark.asyncio
async def test_login_success_and_me(client: AsyncClient, db_session: AsyncSession):
    user = User(
        email="test@fastui.in",
        hashed_password=get_password_hash("password"),
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()

    res = await client.post("/auth/login", json={
        "email": "test@fastui.in",
        "password": "password"
    })
    assert res.status_code == 200
    assert res.json()["user"]["email"] == "test@fastui.in"
    assert "access_token" in res.cookies

    # Query /auth/me with the set cookie
    me_res = await client.get("/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "test@fastui.in"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    res = await client.post("/auth/login", json={
        "email": "unknown@fastui.in",
        "password": "wrongpassword"
    })
    assert res.status_code == 401
