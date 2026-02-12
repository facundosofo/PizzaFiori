"""
JWT Service for generating and validating tokens using python-jose
"""

from datetime import datetime, timedelta
from jose import JWTError, jwt

from app.infrastructure.config.settings import settings


class JWTService:
    """Service for handling JWT token operations."""

    @staticmethod
    def generate_token(
        user_id: int,
        username: str,
        role: str,
        custom_expires_minutes: int | None = None,
    ) -> dict:
        """
        Generate JWT token with expiration based on user role.

        Args:
            user_id: ID of the user
            username: Username of the user
            role: Role of the user (ADMIN, USER, MODERATOR, etc.)
            custom_expires_minutes: Override duration (for testing)

        Returns:
            Dictionary with:
            - token: JWT token string
            - expires_in: Seconds until expiration
            - expires_at: Timestamp (ms) when token expires
        """

        # Determine expiration duration based on role or custom value
        if custom_expires_minutes:
            duration_minutes = custom_expires_minutes
        else:
            duration_minutes = settings.jwt_token_durations.get(
                role, settings.jwt_access_token_expire_minutes
            )

        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=duration_minutes)

        # Create JWT payload
        payload = {
            "sub": str(user_id),  # Subject (user ID)
            "username": username,
            "role": role,
            "exp": expires_at,  # Expiration time
            "iat": now,  # Issued at time
            "type": "access",  # Token type
        }

        # Encode token
        token = jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

        return {
            "token": token,
            "expires_in": int(duration_minutes * 60),  # In seconds for frontend
            "expires_at": int(expires_at.timestamp() * 1000),  # Timestamp in ms
        }

    @staticmethod
    def decode_token(token: str) -> dict:
        """
        Decode and validate JWT token.

        Args:
            token: JWT token string to decode

        Returns:
            Decoded token payload

        Raises:
            ValueError: If token is invalid, expired, or incorrectly signed
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm],
            )
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid or expired token: {str(e)}")

    @staticmethod
    def extract_bearer_token(auth_header: str | None) -> str | None:
        """
        Extract JWT token from Authorization header.

        Expected format: "Authorization: Bearer <token>"

        Args:
            auth_header: Authorization header value

        Returns:
            Token string if valid Bearer header, None otherwise
        """
        if not auth_header:
            return None

        if not auth_header.startswith("Bearer "):
            return None

        return auth_header.split(" ", 1)[1]
