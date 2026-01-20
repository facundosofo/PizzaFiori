from __future__ import annotations

from typing import Optional

from app.domain.unit_of_work import AbstractUnitOfWork
from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.repositories.category_repository import (
    SqlAlchemyCategoryRepository,
)
from app.infrastructure.repositories.product_repository import (
    SqlAlchemyProductRepository,
)
from app.infrastructure.repositories.offer_repository import (
    SqlAlchemyOfferRepository,
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=AsyncSessionLocal):
        self.session_factory = session_factory
        self.session = None
        self.product_repo = None
        self.category_repo = None
        self.offer_repo = None

    async def __aenter__(self):
        self.session = self.session_factory()
        self.product_repo = SqlAlchemyProductRepository(self.session)
        self.category_repo = SqlAlchemyCategoryRepository(self.session)
        self.offer_repo = SqlAlchemyOfferRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            await self.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        if self.session:
            await self.session.rollback()


async def get_uow():
    async with SqlAlchemyUnitOfWork() as uow:
        yield uow