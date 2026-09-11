"""FastUI Authentication Schemas & DTOs."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid corporate or personal email")
    password: str = Field(..., min_length=6, description="Strong password (min 6 chars)")


class PasswordUpdateRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New replacement password")


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="Target email to receive reset instructions")


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., description="Cryptographic reset token")
    new_password: str = Field(..., min_length=6, description="New replacement password")


class VerifyOTPRequest(BaseModel):
    email: EmailStr = Field(..., description="User email receiving OTP")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class UserProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, max_length=255, description="Full display name")


class UserSummary(BaseModel):
    id: int
    email: str
    role: str
    name: str | None = None


class TokenResponse(BaseModel):
    message: str
    user: UserSummary


class TokenData(BaseModel):
    user_id: int
    email: str
    role: str
    name: str | None = None

    @property
    def id(self) -> int:
        return self.user_id
