"""
Authentication related Pydantic schemas
"""

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from app.presentation.schemas.user_schemas import UserResponse


# ---------------------------
# Request Models - Auth
# ---------------------------
class LoginRequest(BaseModel):
    """Login request model (credentials in body or Authorization header)"""
    username: str = Field(..., description="Username for login")
    password: str = Field(..., min_length=1, description="Password for login")


class ResetPasswordRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr = Field(..., description="Email for password reset")


class ResetPasswordConfirmRequest(BaseModel):
    """Password reset confirmation with token"""
    token: str = Field(..., description="Reset token from email")
    new_password: str = Field(..., min_length=8, description="New password")


# ---------------------------
# Response Models - Auth
# ---------------------------
class LoginResponse(BaseModel):
    """Login response with JWT token"""
    token: str = Field(..., description="JWT access token")
    expires_in: int = Field(..., description="Seconds until token expiration")
    expires_at: int = Field(..., description="Timestamp (ms) when token expires")
    user: UserResponse
    message: str = "Login successful"


class ResetPasswordResponse(BaseModel):
    """Password reset response"""
    message: str = "Check your email for password reset instructions"


class LogoutResponse(BaseModel):
    """Logout response"""
    message: str = "Logged out successfully"
    timestamp: datetime
