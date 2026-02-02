from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models.offer import Offer
from app.domain.models.offer_item import OfferItem
from app.domain.repositories.offer_repository import AbstractOfferRepository
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyOfferRepository(BaseRepository[Offer], AbstractOfferRepository):

    model = Offer

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def get_by_id(self, offer_id: int) -> Optional[Offer]:
        query = (
            select(Offer)
            .where(Offer.id == offer_id)
            .options(
                selectinload(Offer.productos).selectinload(OfferItem.productos),
                selectinload(Offer.productos).selectinload(OfferItem.categoria),
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list(
        self,
        active: Optional[bool] = None,
    ) -> List[Offer]:
        query = select(Offer).options(
            selectinload(Offer.productos).selectinload(OfferItem.productos),
            selectinload(Offer.productos).selectinload(OfferItem.categoria),
        )

        if active is not None:
            query = query.where(Offer.activo == active)

        query = query.order_by(Offer.fecha_creacion.asc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def replace_items(
        self,
        offer_id: int,
        new_items: List[OfferItem],
    ) -> None:
        await self.session.execute(
            OfferItem.__table__.delete().where(
                OfferItem.oferta_id == offer_id
            )
        )
        for item in new_items:
            item.oferta_id = offer_id
            self.session.add(item)
