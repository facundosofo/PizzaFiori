"""
Shared dependencies for all routers.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional

bearer_scheme = HTTPBearer()


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Dependency to get current authenticated user from request state."""
    _ = credentials
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
