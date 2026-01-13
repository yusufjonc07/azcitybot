"""Add web_message table for dashboard chat

Revision ID: add_web_message_table
Revises: c3d4e5f6g7h8
Create Date: 2026-01-09

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'add_web_message_table'
down_revision = 'c3d4e5f6g7h8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create web_message table
    op.create_table(
        'web_message',
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.VARCHAR(length=20), nullable=False, server_default='text'),
        sa.Column('file_url', sa.VARCHAR(length=1024), nullable=True),
        sa.Column('file_name', sa.VARCHAR(length=255), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('is_from_user', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('support_chat_id', sa.Uuid(), nullable=False),
        sa.Column('sender_id', sa.Uuid(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['support_chat_id'], ['support_chat.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_web_message_support_chat_id', 'web_message', ['support_chat_id'])
    op.create_index('ix_web_message_created_at', 'web_message', ['created_at'])
    op.create_index('ix_web_message_is_read', 'web_message', ['is_read'])


def downgrade() -> None:
    op.drop_index('ix_web_message_is_read', table_name='web_message')
    op.drop_index('ix_web_message_created_at', table_name='web_message')
    op.drop_index('ix_web_message_support_chat_id', table_name='web_message')
    op.drop_table('web_message')
