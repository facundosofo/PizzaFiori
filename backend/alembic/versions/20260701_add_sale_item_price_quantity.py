"""Add base portion quantity to sale items

Revision ID: 20260701_sale_price_qty
Revises: 20260701_add_numeric_quantities
Create Date: 2026-07-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260701_sale_price_qty'
down_revision = '20260701_add_numeric_quantities'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('VentaItems', sa.Column('precio_cantidad', sa.Numeric(10, 3), nullable=True))


def downgrade() -> None:
    op.drop_column('VentaItems', 'precio_cantidad')
