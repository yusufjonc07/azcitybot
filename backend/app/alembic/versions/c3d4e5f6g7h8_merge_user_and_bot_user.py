"""Merge bot_user table into user table

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-01-09 14:00:00.000000

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3d4e5f6g7h8"
down_revision = "b2c3d4e5f6g7"
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add new columns to user table (from bot_user)
    op.add_column("user", sa.Column("status", sa.Enum("banned", "user", "admin", "super_admin", name="userstatus", create_type=False), nullable=False, server_default="user"))
    op.add_column("user", sa.Column("lang", sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False, server_default="uz"))
    op.add_column("user", sa.Column("admin_groups", sa.JSON(), nullable=True))
    op.add_column("user", sa.Column("created_at", sa.DateTime(), nullable=True))
    
    # Step 2: Update created_at for existing users
    op.execute("UPDATE \"user\" SET created_at = NOW() WHERE created_at IS NULL")
    
    # Step 3: Migrate data from bot_user to user (merge by telegram_id)
    # For users that exist in both tables, update user with bot_user data
    op.execute("""
        UPDATE "user" u
        SET status = bu.status,
            lang = bu.lang,
            admin_groups = bu.admin_groups,
            created_at = COALESCE(bu.created_at, u.created_at, NOW())
        FROM bot_user bu
        WHERE u.telegram_id = bu.telegram_id
    """)
    
    # Step 4: Insert bot_user records that don't exist in user table
    op.execute("""
        INSERT INTO "user" (id, telegram_id, username, full_name, is_active, is_superuser, status, lang, admin_groups, created_at)
        SELECT bu.id, bu.telegram_id, bu.username, bu.full_name, true, false, bu.status, bu.lang, bu.admin_groups, bu.created_at
        FROM bot_user bu
        WHERE NOT EXISTS (SELECT 1 FROM "user" u WHERE u.telegram_id = bu.telegram_id)
    """)
    
    # Step 5: Update support_chat foreign keys to point to user table
    # First, update user_id references
    op.execute("""
        UPDATE support_chat sc
        SET user_id = u.id
        FROM "user" u, bot_user bu
        WHERE sc.user_id = bu.id AND u.telegram_id = bu.telegram_id
    """)
    
    # Update admin_id references
    op.execute("""
        UPDATE support_chat sc
        SET admin_id = u.id
        FROM "user" u, bot_user bu
        WHERE sc.admin_id = bu.id AND u.telegram_id = bu.telegram_id
    """)
    
    # Step 6: Drop foreign key constraints from support_chat to bot_user
    op.drop_constraint("support_chat_user_id_fkey", "support_chat", type_="foreignkey")
    op.drop_constraint("support_chat_admin_id_fkey", "support_chat", type_="foreignkey")
    
    # Step 7: Create new foreign key constraints to user table
    op.create_foreign_key(
        "support_chat_user_id_fkey", "support_chat", "user",
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "support_chat_admin_id_fkey", "support_chat", "user",
        ["admin_id"], ["id"], ondelete="SET NULL"
    )
    
    # Step 8: Drop bot_user table
    op.drop_index(op.f("ix_bot_user_telegram_id"), table_name="bot_user")
    op.drop_table("bot_user")
    
    # Step 9: Remove server defaults (optional cleanup)
    op.alter_column("user", "status", server_default=None)
    op.alter_column("user", "lang", server_default=None)


def downgrade():
    # Recreate bot_user table
    op.create_table(
        "bot_user",
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("full_name", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column("status", sa.Enum("banned", "user", "admin", "super_admin", name="userstatus", create_type=False), nullable=False),
        sa.Column("lang", sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column("admin_groups", sa.JSON(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bot_user_telegram_id"), "bot_user", ["telegram_id"], unique=True)
    
    # Copy user data back to bot_user (for users with bot-specific data)
    op.execute("""
        INSERT INTO bot_user (id, telegram_id, username, full_name, status, lang, admin_groups, created_at)
        SELECT gen_random_uuid(), telegram_id, username, full_name, status, lang, admin_groups, created_at
        FROM "user"
    """)
    
    # Update support_chat foreign keys back to bot_user
    op.drop_constraint("support_chat_user_id_fkey", "support_chat", type_="foreignkey")
    op.drop_constraint("support_chat_admin_id_fkey", "support_chat", type_="foreignkey")
    
    op.execute("""
        UPDATE support_chat sc
        SET user_id = bu.id
        FROM bot_user bu, "user" u
        WHERE sc.user_id = u.id AND u.telegram_id = bu.telegram_id
    """)
    
    op.execute("""
        UPDATE support_chat sc
        SET admin_id = bu.id
        FROM bot_user bu, "user" u
        WHERE sc.admin_id = u.id AND u.telegram_id = bu.telegram_id
    """)
    
    op.create_foreign_key(
        "support_chat_user_id_fkey", "support_chat", "bot_user",
        ["user_id"], ["id"], ondelete="CASCADE"
    )
    op.create_foreign_key(
        "support_chat_admin_id_fkey", "support_chat", "bot_user",
        ["admin_id"], ["id"], ondelete="SET NULL"
    )
    
    # Remove columns from user table
    op.drop_column("user", "created_at")
    op.drop_column("user", "admin_groups")
    op.drop_column("user", "lang")
    op.drop_column("user", "status")
