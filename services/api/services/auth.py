"""
Backward compatibility re-export module for services.auth
"""
from services.auth_service import (
    TokenData,
    verify_password,
    get_password_hash,
    create_access_token,
    authenticate_user,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
