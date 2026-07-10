"""add performance indexes on article.created, article_keyword.keyword_id, keyword.blocked

Revision ID: l2m3n4o5p6q7
Revises: k1l2m3n4o5p6
Create Date: 2026-04-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'l2m3n4o5p6q7'
down_revision: Union[str, Sequence[str], None] = 'k1l2m3n4o5p6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_article_created', 'article', ['created'])
    op.create_index('ix_article_keyword_keyword_id', 'article_keyword', ['keyword_id'])
    op.execute("CREATE INDEX ix_keyword_not_blocked ON keyword (id) WHERE NOT blocked")


def downgrade() -> None:
    op.drop_index('ix_article_created', table_name='article')
    op.drop_index('ix_article_keyword_keyword_id', table_name='article_keyword')
    op.execute("DROP INDEX IF EXISTS ix_keyword_not_blocked")
