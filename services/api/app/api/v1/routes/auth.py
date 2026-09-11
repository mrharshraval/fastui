"""FastUI Authentication & Identity Route Endpoints."""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.config.settings import settings
from app.domains.auth.schemas import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordUpdateRequest,
    RegisterRequest,
    TokenData,
    TokenResponse,
    UserProfileUpdateRequest,
    UserSummary,
    VerifyOTPRequest,
)
from app.domains.auth.service import AuthService
from app.infrastructure.email.provider import email_service
from app.shared.constants import AUTH_COOKIE_NAME
from app.shared.security import create_access_token

logger = logging.getLogger("fastui.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_auth_cookie(response: Response, token: str) -> None:
    is_production = settings.ENVIRONMENT.lower() == "production"
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _clear_auth_cookie(response: Response) -> None:
    is_production = settings.ENVIRONMENT.lower() == "production"
    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=is_production,
        samesite="lax",
    )
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value="",
        max_age=0,
        expires=0,
        path="/",
        httponly=True,
        secure=is_production,
        samesite="lax",
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    """Registers a new user and dispatches a verification OTP email."""
    new_user, otp_code = await AuthService.register_user(
        session=session, email=req.email, password=req.password
    )

    background_tasks.add_task(
        email_service.send_verification_otp,
        to_email=new_user.email,
        otp_code=otp_code,
    )

    role_str = new_user.role.value if hasattr(new_user.role, "value") else str(new_user.role)
    return TokenResponse(
        message="OTP sent to email. Please verify.",
        user=UserSummary(id=new_user.id, email=new_user.email, role=role_str, name=new_user.name),
    )


@router.post("/verify", response_model=TokenResponse)
async def verify_otp(
    req: VerifyOTPRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    """Verifies email OTP, activates the account, and issues authentication cookie."""
    user = await AuthService.verify_otp(session=session, email=req.email, otp=req.otp)

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email, "role": role_str}
    )
    _set_auth_cookie(response, access_token)

    return TokenResponse(
        message="Account verified and logged in successfully",
        user=UserSummary(id=user.id, email=user.email, role=role_str, name=user.name),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    """Authenticates credentials and sets HttpOnly JWT cookie."""
    user = await AuthService.authenticate_user(
        session=session, email=req.email, password=req.password
    )

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email, "role": role_str}
    )
    _set_auth_cookie(response, access_token)

    return TokenResponse(
        message="Login successful",
        user=UserSummary(id=user.id, email=user.email, role=role_str, name=user.name),
    )


@router.post("/logout")
async def logout(response: Response):
    """Clears access token cookie."""
    _clear_auth_cookie(response)
    return {"status": "logged out"}


@router.get("/me", response_model=TokenData)
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """Returns currently authenticated user session details."""
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    response: Response,
    current_user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Deletes current user's account and clears session cookie."""
    await AuthService.delete_account(session=session, user_id=current_user.user_id)
    _clear_auth_cookie(response)
    return Response(status_code=status.HTTP_204_NO_CONTENT, headers=dict(response.headers))


@router.patch("/me", response_model=TokenData)
async def update_profile(
    req: UserProfileUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Updates user display name."""
    user = await AuthService.update_profile(
        session=session, user_id=current_user.user_id, name=req.name
    )
    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    return TokenData(user_id=user.id, email=user.email, role=role_str, name=user.name)


@router.put("/password")
async def update_password(
    req: PasswordUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    """Updates the password for the currently logged-in user."""
    await AuthService.update_password(
        session=session,
        user_id=current_user.user_id,
        current_password=req.current_password,
        new_password=req.new_password,
    )
    return {"message": "Password updated successfully"}


@router.post("/password/reset/request")
async def request_password_reset(
    req: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    """Dispatches a password reset link to user's email."""
    result = await AuthService.create_password_reset_request(session=session, email=req.email)
    if result:
        user, token = result
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        background_tasks.add_task(
            email_service.send_password_reset,
            to_email=user.email,
            reset_link=reset_link,
        )
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/password/reset/confirm")
async def confirm_password_reset(
    req: PasswordResetConfirm,
    session: AsyncSession = Depends(get_db),
):
    """Resets password using a valid reset token."""
    await AuthService.confirm_password_reset(
        session=session, token=req.token, new_password=req.new_password
    )
    return {"message": "Password has been reset successfully"}
