from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.domain.models.app_config import AppConfig


class AbstractAppConfigRepository(ABC):
    @abstractmethod
    async def get_by_key(self, key: str) -> Optional[AppConfig]:
        ...

    @abstractmethod
    async def set_value(self, key: str, value: str) -> AppConfig:
        ...
