"""add keyword.embedding

Revision ID: o5p6q7r8s9t0
Revises: n4o5p6q7r8s9
Create Date: 2026-04-23 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector


revision: str = 'o5p6q7r8s9t0'
down_revision: Union[str, Sequence[str], None] = 'n4o5p6q7r8s9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('keyword', sa.Column('embedding', Vector(384), nullable=True))


def downgrade() -> None:
    op.drop_column('keyword', 'embedding')
