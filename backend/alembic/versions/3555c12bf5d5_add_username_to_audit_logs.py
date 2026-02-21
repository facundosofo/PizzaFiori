"""add_username_to_audit_logs

Revision ID: 3555c12bf5d5
Revises: 08f32f7d7a7d
Create Date: 2026-02-21 18:51:26.177172

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3555c12bf5d5'
down_revision: Union[str, Sequence[str], None] = '08f32f7d7a7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Agregar columna username a audit_logs
    op.add_column('audit_logs', sa.Column('username', sa.String(100), nullable=False, server_default='unknown'))
    # Remover el server_default después de agregar la columna
    op.alter_column('audit_logs', 'username', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    # Eliminar columna username
    op.drop_column('audit_logs', 'username')
