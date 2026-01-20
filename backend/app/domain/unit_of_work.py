from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.repositories.category_repository import AbstractCategoryRepository
from app.domain.repositories.product_repository import AbstractProductRepository


class AbstractUnitOfWork(ABC):
    product_repo: AbstractProductRepository
    category_repo: AbstractCategoryRepository

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