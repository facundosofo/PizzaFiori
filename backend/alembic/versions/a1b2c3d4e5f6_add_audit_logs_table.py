"""Add audit_logs table and category timestamps

Revision ID: a1b2c3d4e5f6
Revises: 76d411b38a74
Create Date: 2026-02-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '76d411b38a74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema:
    1. Create audit_logs table
    2. Add timestamps to Categorias table
    """
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('changes', JSONB, nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('correlation_id', sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['Usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for audit_logs
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'], unique=False)
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'], unique=False)
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'], unique=False)
    op.create_index('ix_audit_logs_entity_id', 'audit_logs', ['entity_id'], unique=False)
    op.create_index('ix_audit_logs_correlation_id', 'audit_logs', ['correlation_id'], unique=False)
    
    # Create composite indexes for common queries
    op.create_index(
        'ix_audit_entity_timestamp',
        'audit_logs',
        ['entity_type', 'entity_id', 'timestamp'],
        unique=False
    )
    op.create_index(
        'ix_audit_user_timestamp',
        'audit_logs',
        ['user_id', 'timestamp'],
        unique=False
    )
    
    # Add timestamp DESC index for recent queries
    op.execute('CREATE INDEX ix_audit_timestamp_desc ON audit_logs (timestamp DESC)')
    
    # Add timestamps to Categorias table
    op.add_column(
        'Categorias',
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )
    op.add_column(
        'Categorias',
        sa.Column('fecha_actualizacion', sa.DateTime(), nullable=False, server_default=sa.text('NOW()'))
    )


def downgrade() -> None:
    """
    Downgrade schema:
    1. Remove timestamps from Categorias table
    2. Drop audit_logs table and indexes
    """
    # Remove timestamps from Categorias
    op.drop_column('Categorias', 'fecha_actualizacion')
    op.drop_column('Categorias', 'fecha_creacion')
    
    # Drop composite indexes
    op.execute('DROP INDEX IF EXISTS ix_audit_timestamp_desc')
    op.drop_index('ix_audit_user_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_entity_timestamp', table_name='audit_logs')
    
    # Drop simple indexes
    op.drop_index('ix_audit_logs_correlation_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_user_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_timestamp', table_name='audit_logs')
    
    # Drop audit_logs table
    op.drop_table('audit_logs')
