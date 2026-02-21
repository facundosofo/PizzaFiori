"""
User Management Router - Handles registration, user management, and profile updates
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from dependency_injector.wiring import inject, Provide
import structlog

from app.application.user_service import UserService
from app.containers import Container
from app.presentation.schemas.user_schemas import (
    RegisterRequest,
    RegisterResponse,
    UserResponse,
    UserDetailResponse,
    UserListResponse,
    CurrentUserResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    UpdateUserRequest,
)
from app.infrastructure.logging import get_logger
from app.presentation.routers.dependencies import get_current_user, require_admin


router = APIRouter(tags=["User Management"])
logger = get_logger(__name__)


@router.post(
    "/users",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register User",
    description="Register a new user account",
    responses={
        409: {"description": "Username or email already exists"},
        422: {"description": "Invalid password or data"},
    },
)
@inject
async def register(
    request_obj: Request,
    request: RegisterRequest,
    service: UserService = Depends(Provide[Container.user_service]),
):
    """Register a new user account."""
    # Extraer IP para auditoría
    ip_address = request_obj.client.host if request_obj.client else None
    correlation_id = getattr(request_obj.state, 'correlation_id', None)
    
    result = await service.register_user(
        username=request.username,
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
        created_by_user_id=None,  # Auto-registro
        ip_address=ip_address,
        correlation_id=correlation_id,
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


@router.get(
    "/users/me",
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


@router.post(
    "/users/me/change-password",
    response_model=ChangePasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Change Password",
    description="Change password for authenticated user",
    responses={
        400: {"description": "Invalid old password"},
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


@router.get(
    "/users",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    summary="List All Users",
    description="Get a list of all users (Admin only)",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
    },
)
@inject
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: str | None = None,
    admin_user: dict = Depends(require_admin),
    service: UserService = Depends(Provide[Container.user_service]),
):
    """
    Get a list of all users.
    
    Requires authentication and admin role.
    
    Query parameters:
    - skip: Number of users to skip (default: 0)
    - limit: Maximum number of users to return (default: 100)
    - role: Optional filter by user role
    """
    result = await service.get_all_users(skip=skip, limit=limit, role_filter=role)

    if result.error:
        logger.error("Error listing users", error=result.error)
        raise HTTPException(status_code=result.status_code, detail=result.error)

    users = result.value
    
    logger.info(
        "Users listed",
        count=len(users),
        skip=skip,
        limit=limit,
        requested_by=admin_user.get("id"),
    )

    return UserListResponse(
        users=[UserDetailResponse.model_validate(user) for user in users],
        total=len(users),
        skip=skip,
        limit=limit,
    )


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get User Details",
    description="Get detailed information about a specific user (Admin only)",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
        404: {"description": "User not found"},
    },
)
@inject
async def get_user_details(
    user_id: int,
    admin_user: dict = Depends(require_admin),
    service: UserService = Depends(Provide[Container.user_service]),
):
    """Get detailed information about a specific user."""
    result = await service.get_user(user_id)

    if result.error:
        logger.warning("User not found", user_id=user_id)
        raise HTTPException(status_code=result.status_code, detail=result.error)

    user = result.value

    logger.info(
        "User details retrieved",
        user_id=user_id,
        requested_by=admin_user.get("id"),
    )

    return UserResponse.model_validate(user)


@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User",
    description="Update user information (Admin only)",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
        404: {"description": "User not found"},
    },
)
@inject
async def update_user(
    request: Request,
    user_id: int,
    data: UpdateUserRequest,
    admin_user: dict = Depends(require_admin),
    service: UserService = Depends(Provide[Container.user_service]),
):
    """Update user information."""
    # Convert to dict and filter out None values
    update_data = data.model_dump(exclude_unset=True)
    
    # Contexto de auditoría
    updated_by_user_id = admin_user["id"]
    ip_address = request.client.host if request.client else None
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    result = await service.update_user(
        user_id,
        update_data,
        updated_by_user_id=updated_by_user_id,
        ip_address=ip_address,
        correlation_id=correlation_id,
    )

    if result.error:
        logger.warning("Failed to update user", user_id=user_id, error=result.error)
        raise HTTPException(status_code=result.status_code, detail=result.error)

    user = result.value

    logger.info(
        "User updated successfully",
        user_id=user_id,
        updated_by=admin_user.get("id"),
    )

    return UserResponse.model_validate(user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User",
    description="Delete a user (Admin only)",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
        404: {"description": "User not found"},
    },
)
@inject
async def delete_user(
    request: Request,
    user_id: int,
    admin_user: dict = Depends(require_admin),
    service: UserService = Depends(Provide[Container.user_service]),
):
    """Delete a user."""
    # Contexto de auditoría
    deleted_by_user_id = admin_user["id"]
    ip_address = request.client.host if request.client else None
    correlation_id = getattr(request.state, 'correlation_id', None)
    
    result = await service.delete_user(
        user_id,
        deleted_by_user_id=deleted_by_user_id,
        ip_address=ip_address,
        correlation_id=correlation_id,
    )

    if result.error:
        logger.warning("Failed to delete user", user_id=user_id, error=result.error)
        raise HTTPException(status_code=result.status_code, detail=result.error)

    logger.info(
        "User deleted successfully",
        user_id=user_id,
        deleted_by=admin_user.get("id"),
    )

    return None


@router.post(
    "/users/{user_id}/unlock",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Unlock User",
    description="Unlock a locked user account (Admin only)",
    responses={
        401: {"description": "Not authenticated"},
        403: {"description": "Admin access required"},
        404: {"description": "User not found"},
    },
)
@inject
async def unlock_user(
    user_id: int,
    admin_user: dict = Depends(require_admin),
    service: UserService = Depends(Provide[Container.user_service]),
):
    """Unlock a locked user account."""
    result = await service.unlock_user_account(user_id)

    if result.error:
        logger.warning("Failed to unlock user", user_id=user_id, error=result.error)
        raise HTTPException(status_code=result.status_code, detail=result.error)

    user = result.value

    logger.info(
        "User account unlocked",
        user_id=user_id,
        unlocked_by=admin_user.get("id"),
    )

    return UserResponse.model_validate(user)

