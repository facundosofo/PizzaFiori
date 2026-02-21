"""remove_ip_address_from_audit_logs

Revision ID: 08f32f7d7a7d
Revises: a1b2c3d4e5f6
Create Date: 2026-02-21 18:42:17.895171

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08f32f7d7a7d'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Eliminar columna ip_address de audit_logs
    op.drop_column('audit_logs', 'ip_address')


def downgrade() -> None:
    """Downgrade schema."""
    # Restaurar columna ip_address
    op.add_column('audit_logs', sa.Column('ip_address', sa.String(45), nullable=True))
