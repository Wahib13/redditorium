"""article-fk-source-to-feed

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('article') as batch_op:
        batch_op.add_column(sa.Column('feed_url', sa.String(), nullable=True))
        batch_op.create_foreign_key('fk_article_feed_url', 'feed', ['feed_url'], ['url'])
        batch_op.drop_column('source_id')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('article') as batch_op:
        batch_op.add_column(sa.Column('source_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_article_source_id', 'source', ['source_id'], ['id'])
        batch_op.drop_column('feed_url')
