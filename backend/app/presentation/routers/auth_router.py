"""
Authentication Router - Handles login, registration, and password operations
"""

import base64
from fastapi import APIRouter, Depends, HTTPException, Request, status
from dependency_injector.wiring import inject, Provide
import structlog

from app.application.user_service import UserService
from app.application.services.jwt_service import JWTService
from app.containers import Container
from app.presentation.schemas.auth_schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    LogoutResponse,
    CurrentUserResponse,
    UserResponse,
)
from app.infrastructure.logging import get_logger


router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)


def get_current_user(request: Request) -> dict:
    """Dependency to get current authenticated user from request state."""
    if not hasattr(request.state, "current_user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return request.state.current_user


def require_admin(request: Request) -> dict:
    """Dependency to require admin role."""
    user = get_current_user(request)
    if user.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate user with username and password (Basic Auth). Returns JWT token.",
    responses={
        401: {"description": "Invalid credentials"},
        423: {"description": "Account locked due to too many failed attempts"},
    },
)
@inject
async def login(
    request: Request,
    service: UserService = Depends(Provide[Container.user_service]),
):
    """
    Login endpoint that accepts Basic Authentication credentials.

    Expected header: Authorization: Basic <base64(username:password)>
    """
    # Extract Basic Auth header
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Basic "):
        logger.warning("Login attempt without Basic Auth header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    try:
        # Decode Base64 credentials
        base64_credentials = auth_header.split(" ", 1)[1]
        credentials = base64.b64decode(base64_credentials).decode("utf-8")
        username, password = credentials.split(":", 1)
    except (ValueError, IndexError, Exception) as e:
        logger.warning("Invalid Basic Auth format", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format",
        )

    # Authenticate user
    result = await service.authenticate_user(username, password)

    if result.error:
        logger.warning(
            "Login failed",
            username=username,
            status_code=result.status_code,
        )
        raise HTTPException(status_code=result.status_code, detail=result.error)

    user = result.value

    # Generate JWT token
    jwt_data = JWTService.generate_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
    )

    logger.info(
        "User logged in successfully",
        user_id=user.id,
        username=username,
    )

    return LoginResponse(
        token=jwt_data["token"],
        expires_in=jwt_data["expires_in"],
        expires_at=jwt_data["expires_at"],
        user=UserResponse.model_validate(user),
        message="Login successful",
    )


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new user account",
    responses={
        409: {"description": "Username or email already exists"},
        422: {"description": "Invalid password or data"},
    },
)
@inject
async def register(
    request: RegisterRequest,
    service: UserService = Depends(Provide[Container.user_service]),
):
    """Register a new user account."""
    result = await service.register_user(
        username=request.username,
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
    )

    if result.error:
        logger.warning(
            "Registration failed",
            username=request.username,
            error=result.error,
        )
        raise HTTPException(status_code=result.status_code, detail=result.error)

    logger.info(
        "User registered successfully",
        user_id=result.value.id,
        username=request.username,
    )

    return RegisterResponse(
        user=UserResponse.model_validate(result.value),
        message="Registration successful. Please login.",
    )


@router.post(
    "/change-password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Change Password",
    description="Change password for authenticated user",
    responses={
        401: {"description": "Invalid old password"},
        422: {"description": "Invalid new password"},
    },
)
@inject
async def change_password(
    request: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(Provide[Container.user_service]),
):
    """Change password for the current authenticated user."""
    result = await service.change_password(
        user_id=current_user["id"],
        old_password=request.old_password,
        new_password=request.new_password,
    )

    if result.error:
        logger.warning(
            "Password change failed",
            user_id=current_user["id"],
            error=result.error,
        )
        raise HTTPException(status_code=result.status_code, detail=result.error)

    logger.info(
        "Password changed successfully",
        user_id=current_user["id"],
    )

    return ChangePasswordResponse(message="Password changed successfully")


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request Password Reset",
    description="Request a password reset email",
)
async def reset_password(request: ResetPasswordRequest):
    """
    Request password reset.
    
    Note: This is a simplified implementation.
    In production, implement email sending and token generation.
    """
    # TODO: Implement email sending with reset token
    logger.info(
        "Password reset requested",
        email=request.email,
    )

    return ResetPasswordResponse(
        message="If that email address is in our database, we will send you an "
        "email to reset your password."
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout",
    description="Logout the current user and invalidate all previous tokens",
)
@inject
async def logout(
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(Provide[Container.user_service]),
):
    """
    Logout the current user.
    
    Updates last_logout_at to invalidate all tokens issued before logout time.
    """
    from datetime import datetime

    result = await service.get_user(current_user["id"])

    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)

    user = result.value

    # Update last_logout_at to invalidate all previous tokens
    from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork

    async with SqlAlchemyUnitOfWork() as uow:
        await uow.users.update(user)
        user.last_logout_at = datetime.utcnow()
        await uow.users.update(user)
        await uow.commit()

    logger.info(
        "User logged out successfully",
        user_id=current_user["id"],
    )

    return LogoutResponse(
        message="Logged out successfully",
        timestamp=datetime.utcnow(),
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User",
    description="Get information about the currently authenticated user",
)
@inject
async def get_me(
    current_user: dict = Depends(get_current_user),
    service: UserService = Depends(Provide[Container.user_service]),
):
    """Get the current authenticated user's information."""
    result = await service.get_user(current_user["id"])

    if result.error:
        raise HTTPException(status_code=result.status_code, detail=result.error)

    user = result.value

    return CurrentUserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name,
    )
