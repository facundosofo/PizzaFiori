"""stock visibility and per product

Revision ID: b3f2a1c9e8d7
Revises: 740a1792f26a
Create Date: 2026-03-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3f2a1c9e8d7'
down_revision = '740a1792f26a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add stock_visible and stock_por_producto to productos_categorias
    op.add_column(
        'productos_categorias',
        sa.Column('stock_visible', sa.Boolean(), nullable=False, server_default=sa.text('true'))
    )
    op.add_column(
        'productos_categorias',
        sa.Column('stock_por_producto', sa.Boolean(), nullable=False, server_default=sa.text('false'))
    )

    # Create stock_productos table
    op.create_table(
        'stock_productos',
        sa.Column('producto_id', sa.Integer(), sa.ForeignKey('Productos.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('cantidad', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('umbral_amarillo', sa.Integer(), nullable=True),
        sa.Column('umbral_rojo', sa.Integer(), nullable=True),
        sa.Column('fecha_actualizacion', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_stock_productos_id', 'stock_productos', ['producto_id'])


def downgrade() -> None:
    op.drop_index('ix_stock_productos_id', table_name='stock_productos')
    op.drop_table('stock_productos')
    op.drop_column('productos_categorias', 'stock_por_producto')
    op.drop_column('productos_categorias', 'stock_visible')
