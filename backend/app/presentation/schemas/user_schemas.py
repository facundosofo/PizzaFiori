"""
User Management related Pydantic schemas
"""

from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator
from typing import Optional
from datetime import datetime


# ---------------------------
# Request Models - User
# ---------------------------
class RegisterRequest(BaseModel):
    """User registration request model"""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., max_length=255, description="Valid email address")
    password: str = Field(..., min_length=8, description="Password (8+ chars, 1 uppercase, 1 number)")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    role: str = Field(default="USER", min_length=1, max_length=20, description="User role (ADMIN or USER)")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v.isalnum():
            raise ValueError('Username must be alphanumeric')
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (8+ chars, 1 uppercase, 1 number)")

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


class UpdateUserRequest(BaseModel):
    """Update user request model"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=255)
    role: Optional[str] = None


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
    created_at: datetime
    updated_at: datetime


class UserDetailResponse(UserResponse):
    """Detailed user response with additional fields"""
    failed_login_attempts: int
    locked_until: Optional[datetime] = None


class UserListResponse(BaseModel):
    """List of users response"""
    users: list[UserDetailResponse]
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


class RegisterResponse(BaseModel):
    """Registration response"""
    user: UserResponse
    message: str = "Registration successful"


class ChangePasswordResponse(BaseModel):
    """Change password response"""
    message: str = "Password changed successfully"
