"""Add surcharge fields to Ventas table

Revision ID: add_surcharge_fields
Revises: add_app_config
Create Date: 2026-05-13 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_surcharge_fields'
down_revision: str = 'add_app_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('Ventas', sa.Column('porcentaje_recargo', sa.Numeric(precision=5, scale=2), nullable=True))
    op.add_column('Ventas', sa.Column('monto_recargo', sa.Numeric(precision=10, scale=2), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('Ventas', 'monto_recargo')
    op.drop_column('Ventas', 'porcentaje_recargo')