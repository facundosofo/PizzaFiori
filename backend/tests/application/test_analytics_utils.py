"""Tests for analytics utilities."""

from decimal import Decimal

from app.application.analytics_utils import (
    format_mixed_fraction_quantity,
    infer_fraction_denominator,
    resolve_fraction_denominator,
)


def test_infer_fraction_denominator_uses_fractional_base_quantity():
    denominator = infer_fraction_denominator(base_quantity=Decimal("0.5"))

    assert denominator == 2


def test_format_mixed_fraction_quantity_half_with_denominator_2():
    display = format_mixed_fraction_quantity(Decimal("0.5"), denominator=2)

    assert display == "1/2"


def test_resolve_fraction_denominator_uses_common_denominator_for_mixed_fractions():
    denominator = resolve_fraction_denominator(2, 4, 8)

    assert denominator == 8
