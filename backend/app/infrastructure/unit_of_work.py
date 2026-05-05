from __future__ import annotations

from typing import Optional

from app.domain.unit_of_work import AbstractUnitOfWork
from app.infrastructure.database import AsyncSessionLocal
from app.infrastructure.repositories.audit_repository import (
    SqlAlchemyAuditRepository,
)
from app.infrastructure.repositories.product_category_repository import (
    SqlAlchemyProductCategoryRepository,
)
from app.infrastructure.repositories.product_repository import (
    SqlAlchemyProductRepository,
)
from app.infrastructure.repositories.offer_repository import (
    SqlAlchemyOfferRepository,
)
from app.infrastructure.repositories.sale_repository import (
    SqlAlchemySaleRepository,
)
from app.infrastructure.repositories.sequence_repository import (
    SqlAlchemySequenceRepository
)
from app.infrastructure.repositories.user_repository import (
    SqlAlchemyUserRepository,
)
from app.infrastructure.repositories.expense_category_repository import (
    SqlAlchemyExpenseCategoryRepository,
)
from app.infrastructure.repositories.expense_repository import (
    SqlAlchemyExpenseRepository,
)
from app.infrastructure.repositories.category_stock_repository import (
    SqlAlchemyCategoryStockRepository,
)
from app.infrastructure.repositories.product_stock_repository import (
    SqlAlchemyProductStockRepository,
)


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=AsyncSessionLocal):
        self.session_factory = session_factory
        self.session = None
        self.product_repo = None
        self.product_category_repo = None
        self.offer_repo = None
        self.sale_repo = None
        self.sequence_repo = None
        self.users = None
        self.audit_repo = None
        self.expense_category_repo = None
        self.expense_repo = None
        self.stock_repo = None
        self.product_stock_repo = None

    async def __aenter__(self):
        self.session = self.session_factory()
        self.product_repo = SqlAlchemyProductRepository(self.session)
        self.product_category_repo = SqlAlchemyProductCategoryRepository(self.session)
        self.offer_repo = SqlAlchemyOfferRepository(self.session)
        self.sale_repo = SqlAlchemySaleRepository(self.session)
        self.sequence_repo = SqlAlchemySequenceRepository(self.session)
        self.users = SqlAlchemyUserRepository(self.session)
        self.audit_repo = SqlAlchemyAuditRepository(self.session)
        self.expense_category_repo = SqlAlchemyExpenseCategoryRepository(self.session)
        self.expense_repo = SqlAlchemyExpenseRepository(self.session)
        self.stock_repo = SqlAlchemyCategoryStockRepository(self.session)
        self.product_stock_repo = SqlAlchemyProductStockRepository(self.session)
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