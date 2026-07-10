"""add index on article.url for dedup lookups

Revision ID: q7r8s9t0u1v2
Revises: p6q7r8s9t0u1
Create Date: 2026-07-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'q7r8s9t0u1v2'
down_revision: Union[str, Sequence[str], None] = 'p6q7r8s9t0u1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_article_url', 'article', ['url'])


def downgrade() -> None:
    op.drop_index('ix_article_url', table_name='article')
