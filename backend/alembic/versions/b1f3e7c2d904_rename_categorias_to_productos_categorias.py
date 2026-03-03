"""Rename Categorias to productos_categorias

Revision ID: b1f3e7c2d904
Revises: 015867a7b8d7
Create Date: 2026-02-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1f3e7c2d904'
down_revision: Union[str, Sequence[str], None] = '015867a7b8d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old unique index on the old table name
    op.drop_index('ix_Categorias_nombre', table_name='Categorias')

    # Rename the table
    op.rename_table('Categorias', 'productos_categorias')

    # Recreate the index on the new table name
    op.create_index('ix_productos_categorias_nombre', 'productos_categorias', ['nombre'], unique=True)


def downgrade() -> None:
    # Drop the new index
    op.drop_index('ix_productos_categorias_nombre', table_name='productos_categorias')

    # Rename back
    op.rename_table('productos_categorias', 'Categorias')

    # Recreate the original index
    op.create_index('ix_Categorias_nombre', 'Categorias', ['nombre'], unique=True)
