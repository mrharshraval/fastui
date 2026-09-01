import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.config import settings
from models.database import get_db
from models.schema import User, UserRole
from schemas.auth import (
    LoginRequest, 
    RegisterRequest, 
    TokenResponse, 
    TokenData,
    UserProfileUpdateRequest,
    PasswordUpdateRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    VerifyOTPRequest
)
from services.auth_service import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_user,
    create_password_reset_token,
    verify_password_reset_token,
    verify_password,
    generate_otp
)
from datetime import datetime, timedelta, timezone
from services.email_service import email_service

logger = logging.getLogger("fastui.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
async def register(
    req: RegisterRequest,
    response: Response,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Registers a new user and sets HttpOnly JWT cookie.
    """
    clean_email = req.email.lower().strip()
    logger.info(f"[AUTH:REGISTER] 📥 Step 1: Received signup request for '{clean_email}'")
    
    # Check if user already exists
    stmt = select(User).where(User.email == clean_email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        logger.warning(f"[AUTH:REGISTER] ⚠️ Step 1.1: Email '{clean_email}' is already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate OTP
    otp_code = generate_otp()
    otp_expires = datetime.now(timezone.utc) + timedelta(minutes=10)
    logger.info(f"[AUTH:REGISTER] 🔐 Step 2: Generated secure 6-digit OTP (expires in 10 mins)")
    
    # Create new user
    new_user = User(
        email=clean_email,
        hashed_password=get_password_hash(req.password),
        role=UserRole.SALES,
        is_active=False,
        verification_otp=otp_code,
        verification_otp_expires_at=otp_expires
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    logger.info(f"[AUTH:REGISTER] 💾 Step 3: Saved pending user to database (User ID: {new_user.id})")
    
    # Send OTP Email asynchronously in background task (non-blocking)
    logger.info(f"[AUTH:REGISTER] 📨 Step 4: Dispatching verification OTP to '{clean_email}' via BackgroundTasks")
    await email_service.send_verification_otp(
        to_email=new_user.email,
        otp_code=otp_code,
        background_tasks=background_tasks
    )
    
    logger.info(f"[AUTH:REGISTER] ✨ Step 5: Returning 200 OK to client (instant response)")
    return {
        "message": "OTP sent to email. Please verify.",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "role": new_user.role.value if hasattr(new_user.role, 'value') else str(new_user.role)
        }
    }

@router.post("/verify", response_model=TokenResponse)
async def verify_otp(
    req: VerifyOTPRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Verifies the OTP sent to the user's email and activates the account, 
    returning the auth cookie.
    """
    clean_email = req.email.lower().strip()
    logger.info(f"[AUTH:VERIFY] 📥 Step 1: Verification attempt for '{clean_email}' with submitted OTP")
    
    stmt = select(User).where(User.email == clean_email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"[AUTH:VERIFY] ❌ User '{clean_email}' not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    if user.is_active:
        logger.warning(f"[AUTH:VERIFY] ⚠️ User '{clean_email}' is already active/verified")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account already verified")
        
    if not user.verification_otp or user.verification_otp != req.otp:
        logger.warning(f"[AUTH:VERIFY] ❌ Invalid OTP submitted for '{clean_email}'")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")
        
    if not user.verification_otp_expires_at or user.verification_otp_expires_at < datetime.now(timezone.utc):
        logger.warning(f"[AUTH:VERIFY] ⏱️ OTP expired for '{clean_email}'")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired")
        
    # Mark active and clear OTP
    user.is_active = True
    user.verification_otp = None
    user.verification_otp_expires_at = None
    await db.commit()
    logger.info(f"[AUTH:VERIFY] 🔓 Step 2: User '{clean_email}' successfully verified and activated")
    
    # Generate token and login automatically
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    access_token = create_access_token(data={
        "user_id": user.id,
        "email": user.email,
        "role": role_str
    })
    
    is_production = settings.ENVIRONMENT.lower() == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    logger.info(f"[AUTH:VERIFY] 🍪 Step 3: Issued authenticated session cookie for '{clean_email}'")
    
    return {
        "message": "Account verified and logged in successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": role_str
        }
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticates user and sets HttpOnly JWT cookie.
    Auto-provisions the initial developer admin account if database is fresh.
    """
    user = await authenticate_user(db, req.email, req.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    access_token = create_access_token(data={
        "user_id": user.id,
        "email": user.email,
        "role": role_str
    })
    
    is_production = settings.ENVIRONMENT.lower() == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return {
        "message": "Login successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "role": role_str
        }
    }

@router.post("/logout")
async def logout(response: Response):
    """Clears access token cookie with exact matching production security parameters."""
    is_production = settings.ENVIRONMENT.lower() == "production"
    response.delete_cookie(
        key="access_token",
        path="/",
        httponly=True,
        secure=is_production,
        samesite="lax"
    )
    response.set_cookie(
        key="access_token",
        value="",
        max_age=0,
        expires=0,
        path="/",
        httponly=True,
        secure=is_production,
        samesite="lax"
    )
    return {"status": "logged out"}

@router.get("/me", response_model=TokenData)
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """Returns currently authenticated user session details."""
    return current_user

@router.put("/me", response_model=TokenData)
@router.patch("/me", response_model=TokenData)
async def update_profile(
    req: UserProfileUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates user profile information (such as display name) in the database."""
    user = await db.get(User, current_user.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if req.name is not None:
        user.name = req.name.strip()
        
    await db.commit()
    await db.refresh(user)
    
    role_str = user.role.value if hasattr(user.role, 'value') else str(user.role)
    return TokenData(user_id=user.id, email=user.email, role=role_str, name=user.name)

@router.put("/password")
async def update_password(
    req: PasswordUpdateRequest,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Updates the password for the currently logged-in user."""
    user = await db.get(User, current_user.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    if not verify_password(req.current_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")
        
    user.hashed_password = get_password_hash(req.new_password)
    await db.commit()
    return {"message": "Password updated successfully"}

@router.post("/password/reset/request")
async def request_password_reset(
    req: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Generates a password reset token for a given email and sends an email in the background."""
    clean_email = req.email.lower().strip()
    logger.info(f"[AUTH:RESET_REQ] 📥 Step 1: Received password reset request for '{clean_email}'")
    
    result = await db.execute(select(User).where(User.email == clean_email))
    user = result.scalar_one_or_none()
    
    # Always return success to prevent email enumeration attacks
    if not user:
        logger.info(f"[AUTH:RESET_REQ] 🔒 Step 1.1: Email '{clean_email}' not in database (anti-enumeration response)")
        return {"message": "If that email is registered, a reset link has been sent."}
        
    token = create_password_reset_token(user.email)
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    logger.info(f"[AUTH:RESET_REQ] 🔗 Step 2: Created signed password reset token for '{clean_email}'")
    
    logger.info(f"[AUTH:RESET_REQ] 📨 Step 3: Enqueuing reset email via BackgroundTasks")
    await email_service.send_password_reset(
        to_email=user.email,
        reset_link=reset_link,
        background_tasks=background_tasks
    )
    
    logger.info(f"[AUTH:RESET_REQ] ✨ Step 4: Returned 200 OK to client")
    return {"message": "If that email is registered, a reset link has been sent."}

@router.post("/password/reset/confirm")
async def confirm_password_reset(
    req: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Resets the password using a valid reset token."""
    logger.info(f"[AUTH:RESET_CONFIRM] 📥 Step 1: Validating reset token")
    email = verify_password_reset_token(req.token)
    if not email:
        logger.warning(f"[AUTH:RESET_CONFIRM] ❌ Invalid or expired reset token provided")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")
        
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        logger.warning(f"[AUTH:RESET_CONFIRM] ❌ User '{email}' associated with token not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    user.hashed_password = get_password_hash(req.new_password)
    await db.commit()
    logger.info(f"[AUTH:RESET_CONFIRM] 🔐 Step 2: Password updated successfully for '{email}'")
    
    return {"message": "Password has been reset successfully"}
