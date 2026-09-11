"""FastUI Authentication Domain Service.

Encapsulates all identity verification, user account lifecycle, credential validation,
and OTP handling without any HTTP transport dependencies.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.models import User, UserRole
from app.shared.exceptions import (
    AuthenticationError,
    EntityNotFoundError,
    FastUIException,
    ValidationError,
)
from app.shared.security import (
    create_password_reset_token,
    generate_otp,
    get_password_hash,
    verify_password,
    verify_password_reset_token,
)

logger = logging.getLogger("fastui.auth")


class AuthService:
    """Canonical domain service for User and Authentication operations."""

    @staticmethod
    async def register_user(
        session: AsyncSession,
        email: str,
        password: str,
    ) -> tuple[User, str]:
        """Registers a new user account in pending verification state.

        Returns (User, otp_code).
        """
        clean_email = email.lower().strip()
        logger.info(f"[AUTH:SERVICE] Registration request for '{clean_email}'")

        stmt = select(User).where(User.email == clean_email)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            logger.warning(f"[AUTH:SERVICE] Email '{clean_email}' already exists")
            raise ValidationError("Email already registered")

        otp_code = generate_otp()
        otp_expires = datetime.now(UTC) + timedelta(minutes=10)

        new_user = User(
            email=clean_email,
            hashed_password=get_password_hash(password),
            role=UserRole.SALES,
            is_active=False,
            verification_otp=otp_code,
            verification_otp_expires_at=otp_expires,
            otp_failed_attempts=0,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        logger.info(f"[AUTH:SERVICE] Created pending user {new_user.id} for '{clean_email}'")
        return new_user, otp_code

    @staticmethod
    async def verify_otp(
        session: AsyncSession,
        email: str,
        otp: str,
    ) -> User:
        """Verifies OTP code and activates user account."""
        clean_email = email.lower().strip()
        logger.info(f"[AUTH:SERVICE] Verifying OTP for '{clean_email}'")

        stmt = select(User).where(User.email == clean_email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise EntityNotFoundError("User", clean_email)

        if user.is_active:
            raise ValidationError("Account already verified")

        now = datetime.now(UTC)

        if not user.verification_otp or user.verification_otp != otp.strip():
            user.otp_failed_attempts += 1
            attempts = user.otp_failed_attempts
            if attempts >= 5:
                user.verification_otp = None
                user.verification_otp_expires_at = None
                await session.commit()
                raise FastUIException(
                    message="Maximum verification attempts exceeded. Please request a new OTP.",
                    status_code=429,
                    error_code="TOO_MANY_REQUESTS",
                )
            await session.commit()
            remaining = 5 - attempts
            raise ValidationError(f"Invalid OTP. {remaining} attempt(s) remaining.")

        if not user.verification_otp_expires_at or user.verification_otp_expires_at < now:
            raise ValidationError("OTP has expired")

        user.is_active = True
        user.verification_otp = None
        user.verification_otp_expires_at = None
        user.otp_failed_attempts = 0
        await session.commit()
        await session.refresh(user)

        logger.info(f"[AUTH:SERVICE] User {user.id} ('{clean_email}') activated successfully")
        return user

    @staticmethod
    async def authenticate_user(
        session: AsyncSession,
        email: str,
        password: str,
    ) -> User:
        """Validates credentials and ensures account is active."""
        clean_email = email.lower().strip()
        stmt = select(User).where(User.email == clean_email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive or not found")

        return user

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
        """Fetches active user by primary key."""
        return await session.get(User, user_id)

    @staticmethod
    async def update_profile(
        session: AsyncSession,
        user_id: int,
        name: str | None = None,
    ) -> User:
        """Updates user display name."""
        user = await session.get(User, user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)

        if name is not None:
            user.name = name.strip()

        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def update_password(
        session: AsyncSession,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> None:
        """Validates current password and sets new password."""
        user = await session.get(User, user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)

        if not verify_password(current_password, user.hashed_password):
            raise ValidationError("Incorrect current password")

        user.hashed_password = get_password_hash(new_password)
        await session.commit()

    @staticmethod
    async def create_password_reset_request(
        session: AsyncSession,
        email: str,
    ) -> tuple[User, str] | None:
        """Generates a password reset token for registered users."""
        clean_email = email.lower().strip()
        stmt = select(User).where(User.email == clean_email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return None

        token = create_password_reset_token(user.email)
        return user, token

    @staticmethod
    async def confirm_password_reset(
        session: AsyncSession,
        token: str,
        new_password: str,
    ) -> User:
        """Validates reset token and sets new password."""
        email = verify_password_reset_token(token)
        if not email:
            raise ValidationError("Invalid or expired reset token")

        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise EntityNotFoundError("User", email)

        user.hashed_password = get_password_hash(new_password)
        await session.commit()
        return user

    @staticmethod
    async def delete_account(
        session: AsyncSession,
        user_id: int,
    ) -> None:
        """Unlinks related entities and deletes user account."""
        user = await session.get(User, user_id)
        if not user:
            raise EntityNotFoundError("User", user_id)

        # Unlink foreign keys safely across related tables
        related_tables = ["activities", "outreaches", "reminders", "tasks", "notes"]
        for tbl in related_tables:
            try:
                await session.execute(
                    text(f"UPDATE {tbl} SET user_id = NULL WHERE user_id = :uid"),
                    {"uid": user_id},
                )
            except Exception as e:
                logger.debug(f"Could not unlink {tbl}.user_id: {e}")

        try:
            await session.execute(
                text(
                    "UPDATE prospect_demos SET created_by_user_id = NULL WHERE created_by_user_id = :uid"
                ),
                {"uid": user_id},
            )
        except Exception:
            pass

        await session.delete(user)
        await session.commit()
        logger.info(f"[AUTH:SERVICE] Deleted user {user_id}")
