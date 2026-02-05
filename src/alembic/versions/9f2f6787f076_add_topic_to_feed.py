"""add topic to Feed

Revision ID: 9f2f6787f076
Revises: 4ed04106e0fa
Create Date: 2026-02-05 20:21:45.194571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f2f6787f076'
down_revision: Union[str, Sequence[str], None] = '4ed04106e0fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # 1. Get distinct feed_type values from feed
    distinct_feed_types = conn.execute(
        sa.text("SELECT DISTINCT feed_type FROM feed")
    ).fetchall()

    # 2. Uppercase all existing Topic names
    conn.execute(sa.text("UPDATE topic SET name = UPPER(name)"))

    # 3. For each feed_type, create a Topic if one doesn't already exist
    for (feed_type,) in distinct_feed_types:
        topic_name = feed_type.upper()
        exists = conn.execute(
            sa.text("SELECT id FROM topic WHERE name = :name"),
            {"name": topic_name}
        ).fetchone()
        if not exists:
            conn.execute(
                sa.text("INSERT INTO topic (name) VALUES (:name)"),
                {"name": topic_name}
            )

    # 4. Add topic_id column as nullable first
    op.add_column('feed', sa.Column('topic_id', sa.Integer(), nullable=True))

    # 5. Update existing feeds to set topic_id based on feed_type
    conn.execute(
        sa.text("""
            UPDATE feed
            SET topic_id = (
                SELECT id FROM topic WHERE topic.name = UPPER(feed.feed_type)
            )
        """)
    )

    # 6. Make topic_id NOT NULL and add foreign key constraint
    # SQLite doesn't support ALTER COLUMN, so use batch mode for it
    if conn.dialect.name == 'sqlite':
        with op.batch_alter_table('feed') as batch_op:
            batch_op.alter_column('topic_id', nullable=False)
            batch_op.create_foreign_key('fk_feed_topic', 'topic', ['topic_id'], ['id'])
    else:
        op.alter_column('feed', 'topic_id', nullable=False)
        op.create_foreign_key('fk_feed_topic', 'feed', 'topic', ['topic_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    if conn.dialect.name == 'sqlite':
        with op.batch_alter_table('feed') as batch_op:
            batch_op.drop_constraint('fk_feed_topic', type_='foreignkey')
            batch_op.drop_column('topic_id')
    else:
        op.drop_constraint('fk_feed_topic', 'feed', type_='foreignkey')
        op.drop_column('feed', 'topic_id')
