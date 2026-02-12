from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.user import User
from app.domain.repositories.user_repository import AbstractUserRepository
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyUserRepository(BaseRepository[User], AbstractUserRepository):
    model = User

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        query = select(self.model).where(self.model.username == username)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = select(self.model).where(self.model.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list(self, skip: int = 0, limit: int = 100) -> List[User]:
        """List all users with pagination."""
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def list_by_role(self, role: str, skip: int = 0, limit: int = 100) -> List[User]:
        """List users filtered by role."""
        query = (
            select(self.model)
            .where(self.model.role == role)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
