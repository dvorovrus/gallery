"""add expiration fields to albums

Revision ID: 20260608_add_expiration_fields
Revises: 20260608_add_thumbnail_file_id
Create Date: 2026-06-08 18:23:57.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260608_add_expiration_fields"
down_revision = "20260608_add_thumbnail_file_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "albums",
        sa.Column("expiration_type", sa.String(), nullable=False, server_default="unlimited"),
    )
    op.add_column(
        "albums",
        sa.Column("expires_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "albums",
        sa.Column("auto_delete_scheduled", sa.Boolean(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("albums", "auto_delete_scheduled")
    op.drop_column("albums", "expires_at")
    op.drop_column("albums", "expiration_type")
