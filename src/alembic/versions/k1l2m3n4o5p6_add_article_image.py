"""add article image

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2026-04-21 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'k1l2m3n4o5p6'
down_revision: Union[str, Sequence[str], None] = 'j0k1l2m3n4o5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('article', sa.Column('image', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('article', 'image')
