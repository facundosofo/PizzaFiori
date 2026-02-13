"""Drop last_logout_at column from Usuarios

Revision ID: c1d2e3f4g5h6
Revises: b9e2f1c4a7d3
Create Date: 2026-02-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4g5h6'
down_revision: Union[str, Sequence[str], None] = 'b9e2f1c4a7d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop last_logout_at column - using stateless JWT tokens."""
    op.drop_column('Usuarios', 'last_logout_at')


def downgrade() -> None:
    """Recreate last_logout_at column."""
    op.add_column(
        'Usuarios',
        sa.Column('last_logout_at', sa.DateTime(), nullable=True),
    )
