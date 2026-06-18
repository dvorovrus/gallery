"""add_role_to_users

Revision ID: 41e319a9198e
Revises: 063f91e7e8ef
Create Date: 2026-06-18 15:03:38.393799

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '41e319a9198e'
down_revision: Union[str, Sequence[str], None] = '063f91e7e8ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add role column with default value 'user'
    op.add_column('users', sa.Column('role', sa.String(), nullable=False, server_default='user'))
    
    # Make the first user admin
    op.execute("""
        UPDATE users 
        SET role = 'admin' 
        WHERE id = (SELECT MIN(id) FROM users)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'role')
