"""Add numeric quantity support for sale and stock tables

Revision ID: 20260701_add_numeric_quantities
Revises: eed6d1a89691
Create Date: 2026-07-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260701_add_numeric_quantities'
down_revision = 'eed6d1a89691'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('VentaItems', 'cantidad', type_=sa.Numeric(10, 3), existing_type=sa.Integer(), nullable=False)
    op.alter_column('VentaItemOfertaProductos', 'cantidad', type_=sa.Numeric(10, 3), existing_type=sa.Integer(), nullable=False)
    op.alter_column('stock_productos', 'cantidad', type_=sa.Numeric(10, 3), existing_type=sa.Integer(), nullable=False)
    op.alter_column('stock_categorias', 'cantidad', type_=sa.Numeric(10, 3), existing_type=sa.Integer(), nullable=False)
    op.alter_column('ProductoPrecios', 'cantidad', type_=sa.Numeric(10, 3), existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    op.alter_column('stock_categorias', 'cantidad', type_=sa.Integer(), existing_type=sa.Numeric(10, 3), nullable=False)
    op.alter_column('stock_productos', 'cantidad', type_=sa.Integer(), existing_type=sa.Numeric(10, 3), nullable=False)
    op.alter_column('VentaItemOfertaProductos', 'cantidad', type_=sa.Integer(), existing_type=sa.Numeric(10, 3), nullable=False)
    op.alter_column('VentaItems', 'cantidad', type_=sa.Integer(), existing_type=sa.Numeric(10, 3), nullable=False)
    op.alter_column('ProductoPrecios', 'cantidad', type_=sa.Integer(), existing_type=sa.Numeric(10, 3), nullable=False)
