from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from app.domain.models.app_config import AppConfig
from app.domain.repositories.app_config_repository import AbstractAppConfigRepository
from app.infrastructure.repositories.base import BaseRepository


class SqlAlchemyAppConfigRepository(BaseRepository[AppConfig], AbstractAppConfigRepository):
    model = AppConfig

    async def get_by_key(self, key: str) -> Optional[AppConfig]:
        query = select(self.model).where(self.model.key == key)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def set_value(self, key: str, value: str) -> AppConfig:
        config = await self.get_by_key(key)
        if config:
            config.value = value
            await self.session.flush()
            return config
        else:
            config = AppConfig(key=key, value=value)
            return await self.add(config)