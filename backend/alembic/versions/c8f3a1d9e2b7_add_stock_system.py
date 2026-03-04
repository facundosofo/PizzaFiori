"""add stock system

Revision ID: c8f3a1d9e2b7
Revises: 015867a7b8d7
Create Date: 2026-03-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8f3a1d9e2b7'
down_revision: Union[str, Sequence[str], None] = 'b1f3e7c2d904'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crea la tabla stock_categorias e inicializa registros para categorías existentes."""
    op.create_table(
        'stock_categorias',
        sa.Column('categoria_id', sa.Integer(), sa.ForeignKey('productos_categorias.id'), primary_key=True),
        sa.Column('cantidad', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('alerta_amarilla', sa.Integer(), nullable=True),
        sa.Column('alerta_roja', sa.Integer(), nullable=True),
        sa.Column('fecha_actualizacion', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Inicializar stock en 0 para cada categoría existente
    op.execute(
        """
        INSERT INTO stock_categorias (categoria_id, cantidad, fecha_actualizacion)
        SELECT id, 0, NOW()
        FROM productos_categorias
        ON CONFLICT (categoria_id) DO NOTHING
        """
    )


def downgrade() -> None:
    """Elimina la tabla stock_categorias."""
    op.drop_table('stock_categorias')
