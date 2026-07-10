"""add hnsw index on keyword embedding

Revision ID: p6q7r8s9t0u1
Revises: o5p6q7r8s9t0
Create Date: 2026-04-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'p6q7r8s9t0u1'
down_revision: Union[str, Sequence[str], None] = 'o5p6q7r8s9t0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_keyword_embedding_hnsw "
        "ON keyword USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_keyword_embedding_hnsw")
