"""
Authentication Router - Handles login, logout, and password reset
"""

import base64
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from dependency_injector.wiring import inject, Provide
import structlog

from app.application.user_service import UserService
from app.application.services.jwt_service import JWTService
from app.containers import Container
from app.presentation.schemas.auth_schemas import (
    LoginResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    LogoutResponse,
)
from app.presentation.schemas.user_schemas import UserResponse
from app.infrastructure.logging import get_logger
from app.presentation.routers.dependencies import get_current_user


router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = get_logger(__name__)


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
    description="Logout the current user (clear client-side token)",
)
async def logout(
    current_user: dict = Depends(get_current_user),
):
    """
    Logout the current user.
    
    Note: With stateless JWT tokens, logout clears client-side token.
    The server doesn't maintain a logout state (tokens expire naturally).
    """

    logger.info(
        "User logged out successfully",
        user_id=current_user["id"],
    )

    return LogoutResponse(
        message="Logged out successfully",
        timestamp=datetime.now(),
    )
