"""
JWT Authentication Middleware for validating Bearer tokens.
"""

from datetime import datetime
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from app.application.services.jwt_service import JWTService
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.logging import get_logger


# Routes that don't require authentication
PUBLIC_ROUTES = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/health",
    "/auth/login",
    "/auth/reset-password", #TODO: Implementar endpoint
}


class JWTMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT token validation and user context population."""

    def __init__(self, app, logger=None):
        super().__init__(app)
        self.logger = logger or get_logger("auth.jwt")

    async def dispatch(self, request: Request, call_next):
        """
        Validate JWT token on protected routes and populate request.state.current_user
        """

        # Allow CORS preflight requests through
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip JWT validation for public routes
        if self._is_public_route(request.url.path, request.method):
            return await call_next(request)

        # Extract and validate token
        auth_header = request.headers.get("Authorization")
        token = JWTService.extract_bearer_token(auth_header)

        if not token:
            self.logger.warning(
                "Missing authentication token",
                path=request.url.path,
                method=request.method,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Decode and validate token
            payload = JWTService.decode_token(token)
            user_id = int(payload.get("sub", 0))

            # Verify user still exists
            async with SqlAlchemyUnitOfWork() as uow:
                user = await uow.users.get_by_id(user_id)

                if not user:
                    self.logger.warning(
                        "Token validation failed: user not found",
                        user_id=user_id,
                        path=request.url.path,
                    )
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found",
                    )

            # Populate request state with current user
            request.state.current_user = {
                "id": user_id,
                "username": payload.get("username"),
                "role": payload.get("role", "USER"),
            }

            self.logger.debug(
                "Token validation successful",
                user_id=user_id,
                username=request.state.current_user["username"],
                path=request.url.path,
            )

        except ValueError as e:
            self.logger.warning(
                "Token validation failed: invalid token",
                error=str(e),
                path=request.url.path,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)

    @staticmethod
    def _is_public_route(path: str, method: str = "GET") -> bool:
        """Check if the route is public (doesn't require authentication)."""
        # Exact matches
        if path in PUBLIC_ROUTES:
            return True

        # POST /users is registration (public)
        if path == "/users" and method == "POST":
            return True

        # Prefix matches
        for public_prefix in ["/docs", "/openapi", "/redoc", "/health", "/uploads"]:
            if path.startswith(public_prefix):
                return True

        return False
