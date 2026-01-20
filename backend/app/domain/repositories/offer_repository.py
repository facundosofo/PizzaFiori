from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models.offer import Offer


class AbstractOfferRepository(ABC):

    @abstractmethod
    async def add(self, offer: Offer) -> Offer:
        ...

    @abstractmethod
    async def get_by_id(self, offer_id: int) -> Optional[Offer]:
        ...

    @abstractmethod
    async def list(
        self,
        active: Optional[bool] = None,
    ) -> List[Offer]:
        ...

    @abstractmethod
    async def update(self, offer: Offer) -> Offer:
        ...

    @abstractmethod
    async def refresh(
        self,
        offer: Offer,
        attribute_names: Optional[list] = None,
    ) -> None:
        ...
