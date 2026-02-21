"""remove_user_id_and_correlation_id_from_audit_logs

Revision ID: 22f4180cb52e
Revises: 3555c12bf5d5
Create Date: 2026-02-21 19:03:43.464104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22f4180cb52e'
down_revision: Union[str, Sequence[str], None] = '3555c12bf5d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Remover el índice que referencias a user_id
    op.drop_index('ix_audit_user_timestamp', table_name='audit_logs')
    # Remover la Foreign Key
    op.drop_constraint('audit_logs_user_id_fkey', 'audit_logs', type_='foreignkey')
    # Remover columnas
    op.drop_column('audit_logs', 'user_id')
    op.drop_column('audit_logs', 'correlation_id')
    # Agregar nuevo índice con username
    op.create_index('ix_audit_username_timestamp', 'audit_logs', ['username', 'timestamp'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remover el nuevo índice
    op.drop_index('ix_audit_username_timestamp', table_name='audit_logs')
    # Recrear las columnas
    op.add_column('audit_logs', sa.Column('user_id', sa.INTEGER(), nullable=False))
    op.add_column('audit_logs', sa.Column('correlation_id', sa.VARCHAR(length=36), nullable=True))
    # Recrear la Foreign Key
    op.create_foreign_key('audit_logs_user_id_fkey', 'audit_logs', 'Usuarios', ['user_id'], ['id'])
    # Recrear el índice anterior
    op.create_index('ix_audit_user_timestamp', 'audit_logs', ['user_id', 'timestamp'])
