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
    "/auth/reset-password",
}

# All API route prefixes that require authentication
API_PREFIXES = (
    "/auth/",
    "/auth",
    "/users",
    "/productos",
    "/productos-categorias",
    "/ofertas",
    "/ventas",
    "/dashboard",
    "/audit",
    "/gastos",
    "/gastos-categorias",
    "/stock",
    "/health",
    "/docs",
    "/openapi",
    "/redoc",
    "/uploads",
)


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

        # Check if route is public (doesn't REQUIRE auth) but may ACCEPT auth
        is_public_route = self._is_public_route(request.url.path, request.method)
        
        # Extract token if present
        auth_header = request.headers.get("Authorization")
        token = JWTService.extract_bearer_token(auth_header)

        # If token is present, always validate it
        if token:
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
        
        # If no token and route is NOT public, require authentication
        elif not is_public_route:
            # Browser page refreshes (F5 / direct URL) send Accept: text/html but
            # no Bearer token — they are not API calls.  Let them pass through so
            # the SPA exception handler can serve index.html and React can boot.
            accept = request.headers.get("Accept", "")
            if "text/html" in accept:
                return await call_next(request)

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

        return await call_next(request)

    @staticmethod
    def _is_public_route(path: str, method: str = "GET") -> bool:
        """Check if the route is public (doesn't require authentication)."""
        # Exact matches for known public API routes
        if path in PUBLIC_ROUTES:
            return True

        # If path doesn't start with any known API prefix, it's a frontend
        # static file or SPA route — let it through without auth.
        for prefix in API_PREFIXES:
            if path == prefix or path.startswith(prefix + "/") or path.startswith(prefix):
                return False  # It's an API route — requires auth check

        # Not an API route → it's a frontend asset or SPA page → public
        return True
