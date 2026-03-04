"""rename alerta to umbral in stock_categorias

Revision ID: d3e9f1a2b4c6
Revises: c8f3a1d9e2b7
Create Date: 2026-03-03 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd3e9f1a2b4c6'
down_revision: Union[str, None] = 'c8f3a1d9e2b7'
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('stock_categorias', 'alerta_amarilla', new_column_name='umbral_amarillo')
    op.alter_column('stock_categorias', 'alerta_roja', new_column_name='umbral_rojo')


def downgrade() -> None:
    op.alter_column('stock_categorias', 'umbral_amarillo', new_column_name='alerta_amarilla')
    op.alter_column('stock_categorias', 'umbral_rojo', new_column_name='alerta_roja')
