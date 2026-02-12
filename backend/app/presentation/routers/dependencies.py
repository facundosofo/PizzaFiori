"""
Shared dependencies for all routers.
"""

from fastapi import HTTPException, Request, status


def get_current_user(request: Request) -> dict:
    """Dependency to get current authenticated user from request state."""
    if not hasattr(request.state, "current_user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return request.state.current_user


def require_admin(request: Request) -> dict:
    """Dependency to require admin role (ADMIN)."""
    user = get_current_user(request)
    admin_roles = {"ADMIN"}
    if user.get("role") not in admin_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user
