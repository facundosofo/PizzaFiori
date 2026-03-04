from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.repositories.audit_repository import AbstractAuditRepository
from app.domain.repositories.abstract_category_stock_repository import AbstractCategoryStockRepository
from app.domain.repositories.product_category_repository import AbstractProductCategoryRepository
from app.domain.repositories.product_repository import AbstractProductRepository
from app.domain.repositories.offer_repository import AbstractOfferRepository
from app.domain.repositories.sale_repository import AbstractSaleRepository
from app.domain.repositories.sequence_repository import AbstractSequenceRepository
from app.domain.repositories.user_repository import AbstractUserRepository
from app.domain.repositories.expense_category_repository import AbstractExpenseCategoryRepository
from app.domain.repositories.expense_repository import AbstractExpenseRepository


class AbstractUnitOfWork(ABC):
    product_repo: AbstractProductRepository
    product_category_repo: AbstractProductCategoryRepository
    offer_repo: AbstractOfferRepository
    sale_repo: AbstractSaleRepository
    sequence_repo: AbstractSequenceRepository
    users: AbstractUserRepository
    audit_repo: AbstractAuditRepository
    expense_category_repo: AbstractExpenseCategoryRepository
    expense_repo: AbstractExpenseRepository
    stock_repo: AbstractCategoryStockRepository


    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.rollback()

    @abstractmethod
    async def commit(self) -> None:
        ...

    @abstractmethod
    async def rollback(self) -> None:
        ...