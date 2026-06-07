from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.user import User


class AbstractUserRepository(ABC):
    @abstractmethod
    async def add(self, user: User) -> User:
        """Add a new user to the repository."""
        ...

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        ...

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        ...

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users with pagination."""
        ...

    @abstractmethod
    async def list_by_role(self, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """List users filtered by role."""
        ...

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update user information."""
        ...

    @abstractmethod
    async def delete(self, user: User) -> None:
        """Delete a user."""
        ...

    @abstractmethod
    async def refresh(
        self,
        user: User,
        attribute_names: Optional[list] = None,
    ) -> None:
        """Refresh user instance from database."""
        ...
