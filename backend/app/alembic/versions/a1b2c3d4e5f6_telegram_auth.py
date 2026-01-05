"""Change user auth from email/password to Telegram

Revision ID: a1b2c3d4e5f6
Revises: 1a31ce608336
Create Date: 2026-01-05 12:00:00.000000

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns
    op.add_column("user", sa.Column("telegram_id", sa.BigInteger(), nullable=True))
    op.add_column(
        "user",
        sa.Column(
            "username", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "photo_url", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=True
        ),
    )

    # Drop old columns and indexes
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_column("user", "email")
    op.drop_column("user", "hashed_password")

    # Create new index for telegram_id
    op.create_index(op.f("ix_user_telegram_id"), "user", ["telegram_id"], unique=True)

    # Make telegram_id not nullable after migration
    op.alter_column("user", "telegram_id", nullable=False)


def downgrade():
    # Add back old columns
    op.add_column(
        "user",
        sa.Column(
            "hashed_password",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True
        ),
    )

    # Drop new columns and indexes
    op.drop_index(op.f("ix_user_telegram_id"), table_name="user")
    op.drop_column("user", "photo_url")
    op.drop_column("user", "username")
    op.drop_column("user", "telegram_id")

    # Recreate old index
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
