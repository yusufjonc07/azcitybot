"""Add bot_user, support_chat, and message_map models

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-09 12:00:00.000000

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6g7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    # Create bot_user table
    op.create_table(
        "bot_user",
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("full_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("status", sa.Enum("banned", "user", "admin", "super_admin", name="userstatus"), nullable=False),
        sa.Column("lang", sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column("admin_groups", sa.JSON(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bot_user_telegram_id"), "bot_user", ["telegram_id"], unique=True)

    # Create chat table (for admin dashboard chats)
    op.create_table(
        "chat",
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create support_chat table
    op.create_table(
        "support_chat",
        sa.Column("status", sa.Enum("pending", "active", "cancelled", "finished", name="chatstatus"), nullable=False),
        sa.Column("notified_message_id", sa.BigInteger(), nullable=True),
        sa.Column("notice_message_id", sa.BigInteger(), nullable=True),
        sa.Column("support_group_id", sa.BigInteger(), nullable=True),
        sa.Column("pending_message_ids", sa.JSON(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("admin_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("claimed_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["admin_id"], ["bot_user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["bot_user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create message_map table
    op.create_table(
        "message_map",
        sa.Column("user_message_id", sa.BigInteger(), nullable=False),
        sa.Column("support_message_id", sa.BigInteger(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("chat_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["support_chat.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Drop item table if it exists
    op.execute("DROP TABLE IF EXISTS item CASCADE")


def downgrade():
    op.drop_table("message_map")
    op.drop_table("support_chat")
    op.drop_table("chat")
    op.drop_index(op.f("ix_bot_user_telegram_id"), table_name="bot_user")
    op.drop_table("bot_user")
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS chatstatus")
    # Note: userstatus enum might be shared, don't drop it
