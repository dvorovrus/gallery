"""add thumbnail_file_id to photos

Revision ID: 20260608_add_thumbnail_file_id
Revises: 
Create Date: 2026-06-08 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260608_add_thumbnail_file_id"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "photos",
        sa.Column("thumbnail_file_id", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("photos", "thumbnail_file_id")
