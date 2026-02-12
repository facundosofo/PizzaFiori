from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.repositories.category_repository import AbstractCategoryRepository
from app.domain.repositories.product_repository import AbstractProductRepository
from app.domain.repositories.offer_repository import AbstractOfferRepository
from app.domain.repositories.sale_repository import AbstractSaleRepository
from app.domain.repositories.sequence_repository import AbstractSequenceRepository
from app.domain.repositories.user_repository import AbstractUserRepository


class AbstractUnitOfWork(ABC):
    product_repo: AbstractProductRepository
    category_repo: AbstractCategoryRepository
    offer_repo: AbstractOfferRepository
    sale_repo: AbstractSaleRepository
    sequence_repo: AbstractSequenceRepository
    users: AbstractUserRepository


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