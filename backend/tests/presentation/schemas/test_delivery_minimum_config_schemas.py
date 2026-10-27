from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.presentation.schemas.config_schemas import (
    DeliveryMinimumConfigResponse,
    DeliveryMinimumConfigUpdateRequest,
)


def test_delivery_minimum_config_accepts_non_negative_amount_with_cents():
    config = DeliveryMinimumConfigUpdateRequest(monto_minimo_delivery="13000.50")

    assert config.monto_minimo_delivery == Decimal("13000.50")


@pytest.mark.parametrize("amount", ["-1", "13000.555"])
def test_delivery_minimum_config_rejects_negative_or_excess_precision(amount):
    with pytest.raises(ValidationError):
        DeliveryMinimumConfigUpdateRequest(monto_minimo_delivery=amount)


def test_delivery_minimum_config_response_exposes_amount():
    response = DeliveryMinimumConfigResponse(monto_minimo_delivery="13000")

    assert response.model_dump(mode="json") == {"monto_minimo_delivery": "13000"}
