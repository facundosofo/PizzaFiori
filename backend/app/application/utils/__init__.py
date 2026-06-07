"""
Utilidades para la capa de aplicación.
"""
from app.application.utils.audit_helpers import (
    compute_entity_diff,
    compute_sale_diff,
    entity_to_snapshot,
    sale_to_snapshot,
)

__all__ = [
    "compute_entity_diff",
    "compute_sale_diff",
    "entity_to_snapshot",
    "sale_to_snapshot",
]
