"""Add photo_id to Share model for photo sharing

Revision ID: 6e781f55bb75
Revises: 20260608_add_expiration_fields
Create Date: 2026-06-08 22:36:29.927330

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e781f55bb75'
down_revision: Union[str, Sequence[str], None] = '20260608_add_expiration_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add photo_id column and make album_id nullable for photo sharing
    with op.batch_alter_table('shares', schema=None) as batch_op:
        batch_op.add_column(sa.Column('photo_id', sa.Integer(), nullable=True))
        batch_op.alter_column('album_id',
                   existing_type=sa.INTEGER(),
                   nullable=True)
        batch_op.create_foreign_key('fk_shares_photo_id', 'photos', ['photo_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('shares', schema=None) as batch_op:
        batch_op.drop_constraint('fk_shares_photo_id', type_='foreignkey')
        batch_op.alter_column('album_id',
                   existing_type=sa.INTEGER(),
                   nullable=False)
        batch_op.drop_column('photo_id')
