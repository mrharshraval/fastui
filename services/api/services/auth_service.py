import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import bcrypt
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from models.database import get_db
from models.schema import User, UserRole
from schemas.auth import TokenData
import secrets

def generate_otp() -> str:
    """Generates a secure 6-digit numerical OTP string."""
    return f"{secrets.randbelow(1000000):06d}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plaintext password against a bcrypt hash."""
    try:
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Generates a salt and returns a bcrypt hash string."""
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode('utf-8')

def create_access_token(data: dict) -> str:
    """Encodes JWT with expiration timestamp."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def create_password_reset_token(email: str) -> str:
    """Generates a short-lived JWT for password resets."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=15) # 15 minutes expiry
    to_encode = {"exp": expire, "sub": email, "type": "password_reset"}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def verify_password_reset_token(token: str) -> Optional[str]:
    """Decodes reset token and returns the email if valid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Validates user credentials against database and checks active status."""
    result = await db.execute(select(User).where(User.email == email.strip().lower()))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user

async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> TokenData:
    """
    FastAPI dependency for authenticating incoming requests via cookie or Bearer token.
    Verifies that the user still exists and is active in the database.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
    if not token:
        if settings.ENVIRONMENT.lower() == "development":
            result = await db.execute(select(User).where(User.email == "test@fastui.in"))
            dev_user = result.scalar_one_or_none()
            if not dev_user:
                dev_user = User(
                    email="test@fastui.in",
                    hashed_password=get_password_hash("password"),
                    role=UserRole.ADMIN,
                    is_active=True
                )
                db.add(dev_user)
                await db.commit()
                await db.refresh(dev_user)
            role_str = dev_user.role.value if hasattr(dev_user.role, 'value') else str(dev_user.role)
            return TokenData(user_id=dev_user.id, email=dev_user.email, role=role_str)
        raise credentials_exception
        
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        role: str = payload.get("role")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    return TokenData(user_id=user.id, email=user.email, role=role_str)
