"""
Authentication and User related Pydantic schemas
"""

from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
from typing import Optional
from datetime import datetime


# ---------------------------
# Request Models - Auth
# ---------------------------
class LoginRequest(BaseModel):
    """Login request model (credentials passed in Authorization header)"""
    pass  # Credentials are in the Authorization: Basic header


class RegisterRequest(BaseModel):
    """User registration request model"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password (8+ chars, 1 uppercase, 1 number)")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v


class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (8+ chars, 1 uppercase, 1 number)")


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
    user: "UserResponse"
    message: str = "Login successful"


class RegisterResponse(BaseModel):
    """Registration response"""
    user: "UserResponse"
    message: str = "Registration successful"


class ResetPasswordResponse(BaseModel):
    """Password reset response"""
    message: str = "Check your email for password reset instructions"


class ChangePasswordResponse(BaseModel):
    """Change password response"""
    message: str = "Password changed successfully"


class LogoutResponse(BaseModel):
    """Logout response"""
    message: str = "Logged out successfully"
    timestamp: datetime


# ---------------------------
# Response Models - User
# ---------------------------
class UserResponse(BaseModel):
    """User response model (no password_hash)"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserDetailResponse(UserResponse):
    """Detailed user response with additional fields"""
    failed_login_attempts: int
    locked_until: Optional[datetime] = None
    last_logout_at: Optional[datetime] = None


class UserListResponse(BaseModel):
    """List of users response"""
    users: list[UserResponse]
    total: int
    skip: int
    limit: int


class CurrentUserResponse(BaseModel):
    """Current authenticated user info"""
    id: int
    username: str
    email: str
    role: str
    first_name: str
    last_name: str
