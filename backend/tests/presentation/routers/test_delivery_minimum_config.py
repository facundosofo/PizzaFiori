from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.infrastructure.unit_of_work import get_uow
from app.main import app


@pytest.mark.asyncio
async def test_delivery_minimum_config_defaults_and_persists(async_client):
    stored_values = {}

    async def set_value(key, value):
        stored_values[key] = SimpleNamespace(value=value)
        return stored_values[key]

    unit = SimpleNamespace(
        app_config_repo=SimpleNamespace(
            get_by_key=AsyncMock(side_effect=lambda key: stored_values.get(key)),
            set_value=AsyncMock(side_effect=set_value),
        ),
        commit=AsyncMock(),
    )

    class UnitOfWorkContext:
        async def __aenter__(self):
            return unit

        async def __aexit__(self, *_args):
            return None

    app.dependency_overrides[get_uow] = UnitOfWorkContext

    initial_response = await async_client.get("/config/delivery-minimum")
    assert initial_response.status_code == 200
    assert initial_response.json() == {"monto_minimo_delivery": "13000"}

    update_response = await async_client.put(
        "/config/delivery-minimum",
        json={"monto_minimo_delivery": 12500.5},
    )
    assert update_response.status_code == 200
    assert update_response.json() == {"monto_minimo_delivery": "12500.5"}
    unit.commit.assert_awaited_once()

    saved_response = await async_client.get("/config/delivery-minimum")
    assert saved_response.status_code == 200
    assert saved_response.json() == {"monto_minimo_delivery": "12500.5"}


@pytest.mark.asyncio
async def test_delivery_minimum_config_rejects_negative_amount(async_client):
    response = await async_client.put(
        "/config/delivery-minimum",
        json={"monto_minimo_delivery": -1},
    )

    assert response.status_code == 422
