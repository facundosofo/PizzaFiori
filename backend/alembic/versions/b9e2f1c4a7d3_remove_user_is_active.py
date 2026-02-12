"""Remove is_active from Usuarios

Revision ID: b9e2f1c4a7d3
Revises: add_user_model
Create Date: 2026-02-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9e2f1c4a7d3'
down_revision: Union[str, Sequence[str], None] = 'add_user_model'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop is_active column from Usuarios."""
    # First, drop the default constraint on is_active
    op.execute("ALTER TABLE [Usuarios] DROP CONSTRAINT [DF__Usuarios__is_act__71D1E811]")
    # Then drop the column
    op.drop_column('Usuarios', 'is_active')


def downgrade() -> None:
    """Recreate is_active column in Usuarios."""
    op.add_column(
        'Usuarios',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
    )
