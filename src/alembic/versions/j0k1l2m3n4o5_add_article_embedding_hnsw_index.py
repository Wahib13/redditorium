"""add hnsw index on article embedding

Revision ID: j0k1l2m3n4o5
Revises: i9j0k1l2m3n4
Create Date: 2026-04-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'j0k1l2m3n4o5'
down_revision: Union[str, Sequence[str], None] = 'i9j0k1l2m3n4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_article_embedding_hnsw "
        "ON article USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_article_embedding_hnsw")
