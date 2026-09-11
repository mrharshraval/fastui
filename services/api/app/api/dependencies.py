"""FastUI FastAPI Common Route Dependencies.

Authentication, database session injection, and authorization guards.
"""

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.models import User, UserRole
from app.domains.auth.schemas import TokenData
from app.infrastructure.database.session import get_db
from app.shared.constants import AUTH_COOKIE_NAME
from app.shared.security import decode_access_token


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> TokenData:
    """Authenticates request via HttpOnly cookie or Bearer header and verifies user is active."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token: str | None = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise credentials_exception

    try:
        payload = decode_access_token(token)
        user_id: int | None = payload.get("user_id")
        email: str | None = payload.get("email") or payload.get("sub")
        if user_id is None and email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = None
    if user_id is not None:
        user = await session.get(User, user_id)
    if not user and email is not None:
        stmt = select(User).where(User.email == email)
        res = await session.execute(stmt)
        user = res.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    return TokenData(user_id=user.id, email=user.email, role=role_str, name=user.name)


def require_role(*allowed_roles: UserRole):
    """Guard factory that restricts access to users with specified roles."""

    def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        user_role = current_user.role
        allowed = [r.value for r in allowed_roles]
        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker
