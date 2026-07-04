"""Allow decimal quantities in offer items

Revision ID: 20260703_offer_items_qty
Revises: 20260701_sale_price_qty
Create Date: 2026-07-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260703_offer_items_qty'
down_revision = '20260701_sale_price_qty'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'OfertaItems',
        'cantidad',
        type_=sa.Numeric(10, 3),
        existing_type=sa.Integer(),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        'OfertaItems',
        'cantidad',
        type_=sa.Integer(),
        existing_type=sa.Numeric(10, 3),
        nullable=False,
    )
