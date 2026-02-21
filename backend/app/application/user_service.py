"""
User Service for managing user creation, authentication, and password operations.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List
import structlog
import bcrypt
import re

from app.domain.models.user import User
from app.domain.unit_of_work import AbstractUnitOfWork
from app.infrastructure.config.settings import settings


@dataclass
class ServiceResult:
    value: Optional[User] = None
    error: Optional[str] = None
    status_code: int = 200


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against its hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


class UserService:
    """Service for user management and authentication."""

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        audit_service=None,  # Optional for backward compatibility
        logger: structlog.BoundLogger | None = None,
    ):
        self.uow = uow
        self.audit_service = audit_service
        self.logger = logger or structlog.get_logger(__name__)
        self.settings = settings

    def validate_password(self, password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password against policy.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < self.settings.password_min_length:
            return (
                False,
                f"Password must be at least {self.settings.password_min_length} characters",
            )

        if self.settings.password_require_uppercase and not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if self.settings.password_require_numbers and not re.search(r"\d", password):
            return False, "Password must contain at least one number"

        return True, None

    async def register_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role: str = "USER",
        created_by_user_id: Optional[int] = None,  # Para auditoría
        correlation_id: Optional[str] = None,
    ) -> ServiceResult:
        """
        Register a new user.

        Args:
            username: Unique username
            email: User email
            password: Plain text password
            first_name: User's first name
            last_name: User's last name
            role: User role (default: USER)
            created_by_user_id: ID of user creating this user (for audit)
            correlation_id: Correlation ID (for audit)

        Returns:
            ServiceResult with created user or error
        """
        try:
            # Validate password
            is_valid, error_msg = self.validate_password(password)
            if not is_valid:
                self.logger.warning(
                    "Invalid password for registration",
                    username=username,
                    error=error_msg,
                )
                return ServiceResult(error=error_msg, status_code=422)

            async with self.uow as uow:
                # Check if username already exists
                existing_user = await uow.users.get_by_username(username)
                if existing_user:
                    self.logger.warning(
                        "Username already exists",
                        username=username,
                    )
                    return ServiceResult(
                        error="Username already exists", status_code=409
                    )

                # Check if email already exists
                existing_email = await uow.users.get_by_email(email)
                if existing_email:
                    self.logger.warning(
                        "Email already exists",
                        email=email,
                    )
                    return ServiceResult(error="Email already exists", status_code=409)

                # Create new user
                password_hash = hash_password(password)
                user = User(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                )

                await uow.users.add(user)
                await uow.commit()
                await uow.users.refresh(user)

                # Auditar creación (usar el ID del usuario que lo creó, o el mismo si es auto-registro)
                if self.audit_service:
                    audit_user_id = created_by_user_id if created_by_user_id else user.id
await self.audit_service.log_creation(
                    user_id=audit_user_id,
                    entity_type="User",
                    entity=user,
                        correlation_id=correlation_id,
                    )

                self.logger.info(
                    "User registered successfully",
                    user_id=user.id,
                    username=username,
                    email=email,
                )

                return ServiceResult(value=user, status_code=201)

        except Exception as e:
            self.logger.exception("Error during user registration", exc_info=True)
            await self.uow.rollback()
            return ServiceResult(error=str(e), status_code=500)

    async def authenticate_user(
        self, username: str, password: str
    ) -> ServiceResult:
        """
        Authenticate user with username and password.

        Args:
            username: Username
            password: Plain text password

        Returns:
            ServiceResult with authenticated user or error
        """
        try:
            async with self.uow as uow:
                # Get user by username
                user = await uow.users.get_by_username(username)

                if not user:
                    self.logger.warning(
                        "Login attempt with non-existent username",
                        username=username,
                    )
                    return ServiceResult(
                        error="Invalid credentials", status_code=401
                    )

                # Check account lockout
                if user.locked_until and datetime.now() < user.locked_until:
                    remaining_minutes = (
                        user.locked_until - datetime.now()
                    ).total_seconds() / 60
                    self.logger.warning(
                        "Login attempt on locked account",
                        username=username,
                        remaining_minutes=remaining_minutes,
                    )
                    return ServiceResult(
                        error=f"Account locked. Try again in {int(remaining_minutes)} minutes",
                        status_code=423,
                    )

                # Verify password
                if not verify_password(password, user.password_hash):
                    # Increment failed attempts
                    user.failed_login_attempts = (
                        user.failed_login_attempts or 0
                    ) + 1

                    # Check if should lock account
                    if user.failed_login_attempts >= self.settings.max_login_attempts:
                        user.locked_until = datetime.now() + timedelta(
                            minutes=self.settings.lockout_duration_minutes
                        )
                        self.logger.warning(
                            "Account locked due to too many failed attempts",
                            username=username,
                        )

                    await uow.users.update(user)
                    await uow.commit()

                    self.logger.warning(
                        "Failed login attempt",
                        username=username,
                        failed_attempts=user.failed_login_attempts,
                    )

                    return ServiceResult(
                        error="Invalid credentials", status_code=401
                    )

                # Reset failed attempts on successful login
                user.failed_login_attempts = 0
                user.locked_until = None

                await uow.users.update(user)
                await uow.commit()

                self.logger.info(
                    "User authenticated successfully",
                    user_id=user.id,
                    username=username,
                )

                return ServiceResult(value=user, status_code=200)

        except Exception as e:
            self.logger.exception("Error during authentication", exc_info=True)
            await self.uow.rollback()
            return ServiceResult(error=str(e), status_code=500)

    async def get_user(self, user_id: int) -> ServiceResult:
        """Get user by ID."""
        try:
            async with self.uow as uow:
                user = await uow.users.get_by_id(user_id)

                if not user:
                    return ServiceResult(error="User not found", status_code=404)

                return ServiceResult(value=user, status_code=200)

        except Exception as e:
            self.logger.exception("Error getting user", exc_info=True)
            return ServiceResult(error=str(e), status_code=500)

    async def get_all_users(
        self, skip: int = 0, limit: int = 100, role_filter: Optional[str] = None
    ) -> ServiceResult:
        """Get all users with optional role filtering."""
        try:
            async with self.uow as uow:
                if role_filter:
                    users = await uow.users.list_by_role(
                        role_filter, skip=skip, limit=limit
                    )
                else:
                    users = await uow.users.list(skip=skip, limit=limit)

                return ServiceResult(value=users, status_code=200)

        except Exception as e:
            self.logger.exception("Error getting users", exc_info=True)
            return ServiceResult(error=str(e), status_code=500)

    async def update_user(
        self,
        user_id: int,
        data: dict,
        updated_by_user_id: int,
        correlation_id: Optional[str] = None,
    ) -> ServiceResult:
        """Update user information."""
        try:
            async with self.uow as uow:
                user = await uow.users.get_by_id(user_id)

                if not user:
                    return ServiceResult(error="User not found", status_code=404)

                # Capturar estado anterior
                old_user_dict = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                    'failed_login_attempts': user.failed_login_attempts,
                    'locked_until': user.locked_until,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at,
                }

                # Update allowed fields
                allowed_fields = {
                    "first_name",
                    "last_name",
                    "email",
                }
                for key, value in data.items():
                    if key in allowed_fields and value is not None:
                        setattr(user, key, value)

                await uow.users.update(user)
                await uow.commit()
                await uow.users.refresh(user)

                # Auditar actualización
                if self.audit_service:
                    from app.domain.models.user import User as UserModel
                    old_user = UserModel(**old_user_dict)
                    
                    await self.audit_service.log_update(
                        user_id=updated_by_user_id,
                        entity_type="User",
                        old_entity=old_user,
                        new_entity=user,

                    user_id=user.id,
                )

                return ServiceResult(value=user, status_code=200)

        except Exception as e:
            self.logger.exception("Error updating user", exc_info=True)
            await self.uow.rollback()
            return ServiceResult(error=str(e), status_code=500)

    async def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> ServiceResult:
        """Change user password."""
        try:
            # Validate new password
            is_valid, error_msg = self.validate_password(new_password)
            if not is_valid:
                return ServiceResult(error=error_msg, status_code=422)

            async with self.uow as uow:
                user = await uow.users.get_by_id(user_id)

                if not user:
                    return ServiceResult(error="User not found", status_code=404)

                # Verify old password
                if not verify_password(old_password, user.password_hash):
                    self.logger.warning(
                        "Failed password change attempt - invalid old password",
                        user_id=user_id,
                    )
                    return ServiceResult(
                        error="Invalid old password", status_code=400
                    )

                # Update password
                user.password_hash = hash_password(new_password)

                await uow.users.update(user)
                await uow.commit()

                self.logger.info(
                    "Password changed successfully",
                    user_id=user.id,
                )

                return ServiceResult(value=user, status_code=200)

        except Exception as e:
            self.logger.exception("Error changing password", exc_info=True)
            await self.uow.rollback()
            return ServiceResult(error=str(e), status_code=500)

    async def delete_user(
        self,
        user_id: int,
        deleted_by_user_id: int,
        correlation_id: Optional[str] = None,
    ) -> ServiceResult:
        """Delete a user."""
        try:
            async with self.uow as uow:
                user = await uow.users.get_by_id(user_id)

                if not user:
                    return ServiceResult(error="User not found", status_code=404)

                # Auditar antes de eliminar
                if self.audit_service:
                    await self.audit_service.log_deletion(
                        user_id=deleted_by_user_id,
                        entity_type="User",
                        entity=user,

                await uow.commit()

                self.logger.info(
                    "User deleted successfully",
                    user_id=user.id,
                )

                return ServiceResult(value=None, status_code=204)

        except Exception as e:
            self.logger.exception("Error deleting user", exc_info=True)
            await self.uow.rollback()
            return ServiceResult(error=str(e), status_code=500)

    async def unlock_user_account(self, user_id: int) -> ServiceResult:
        """Unlock a locked user account (admin action)."""
        try:
            async with self.uow as uow:
                user = await uow.users.get_by_id(user_id)

                if not user:
                    return ServiceResult(error="User not found", status_code=404)

                user.locked_until = None
                user.failed_login_attempts = 0

                await uow.users.update(user)
                await uow.commit()

                self.logger.info(
                    "User account unlocked",
                    user_id=user.id,
                )

                return ServiceResult(value=user, status_code=200)

        except Exception as e:
            self.logger.exception("Error unlocking user account", exc_info=True)
            await self.uow.rollback()
            return ServiceResult(error=str(e), status_code=500)
