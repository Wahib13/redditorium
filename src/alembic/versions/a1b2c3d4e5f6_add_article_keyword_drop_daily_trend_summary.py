"""add-article-keyword-drop-daily-trend-summary

Revision ID: a1b2c3d4e5f6
Revises: c58001af9870
Create Date: 2026-04-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'c58001af9870'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'article_keyword',
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('keyword_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['article_id'], ['article.id']),
        sa.ForeignKeyConstraint(['keyword_id'], ['keyword.id']),
        sa.PrimaryKeyConstraint('article_id', 'keyword_id'),
    )

    with op.batch_alter_table('article') as batch_op:
        batch_op.drop_column('daily_trend_summary_id')

    op.drop_table('daily_trend_summary')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        'daily_trend_summary',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['topic_id'], ['topic.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    with op.batch_alter_table('article') as batch_op:
        batch_op.add_column(sa.Column('daily_trend_summary_id', sa.Integer(), nullable=True))

    op.drop_table('article_keyword')
