"""Add User model for authentication

Revision ID: add_user_model
Revises: add_dashboard_indexes
Create Date: 2026-02-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_user_model'
down_revision: Union[str, Sequence[str], None] = 'add_dashboard_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Usuarios table for authentication."""
    
    op.create_table(
        'Usuarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), unique=True, nullable=False),
        sa.Column('email', sa.String(100), unique=True, nullable=False),
        sa.Column('password_hash', sa.Text(), nullable=False),
        sa.Column('first_name', sa.String(50), nullable=False),
        sa.Column('last_name', sa.String(50), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='USER'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('last_logout_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )
    
    # Create indexes for performance
    op.create_index('ix_Usuarios_username', 'Usuarios', ['username'])
    op.create_index('ix_Usuarios_email', 'Usuarios', ['email'])


def downgrade() -> None:
    """Drop Usuarios table."""
    
    op.drop_index('ix_Usuarios_email', 'Usuarios')
    op.drop_index('ix_Usuarios_username', 'Usuarios')
    op.drop_table('Usuarios')
