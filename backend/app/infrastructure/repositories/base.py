from __future__ import annotations

from typing import Generic, List, Optional, TypeVar, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    model: type[T]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, entity: T) -> T:
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def get_by_id(self, entity_id: int) -> Optional[T]:
        query = select(self.model).where(self.model.id == entity_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def list(self) -> List[T]:
        result = await self.session.execute(select(self.model))
        return result.scalars().all()

    async def update(self, entity: T) -> T:
        await self.session.flush()
        return entity

    async def delete(self, entity_or_id: Union[T, int]) -> bool:
        if isinstance(entity_or_id, int):
            entity = await self.get_by_id(entity_or_id)
            if entity is None:
                return False
            await self.session.delete(entity)
        else:
            await self.session.delete(entity_or_id)
        await self.session.flush()
        return True

    async def refresh(
        self,
        entity: T,
        attribute_names: Optional[list] = None,
    ) -> None:
        await self.session.refresh(entity, attribute_names=attribute_names)
