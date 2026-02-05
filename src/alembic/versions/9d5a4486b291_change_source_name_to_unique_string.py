"""change source name to unique string

Revision ID: 9d5a4486b291
Revises: a9da2e8aa252
Create Date: 2026-02-05 20:51:48.894958

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d5a4486b291'
down_revision: Union[str, Sequence[str], None] = 'a9da2e8aa252'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    if conn.dialect.name == 'sqlite':
        with op.batch_alter_table('source') as batch_op:
            batch_op.alter_column('name',
                       existing_type=sa.VARCHAR(length=12),
                       nullable=False)
            batch_op.create_unique_constraint('uq_source_name', ['name'])
    else:
        op.alter_column('source', 'name',
                   existing_type=sa.VARCHAR(length=12),
                   nullable=False)
        op.create_unique_constraint('uq_source_name', 'source', ['name'])


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    if conn.dialect.name == 'sqlite':
        with op.batch_alter_table('source') as batch_op:
            batch_op.drop_constraint('uq_source_name', type_='unique')
            batch_op.alter_column('name',
                       existing_type=sa.VARCHAR(length=12),
                       nullable=True)
    else:
        op.drop_constraint('uq_source_name', 'source', type_='unique')
        op.alter_column('source', 'name',
                   existing_type=sa.VARCHAR(length=12),
                   nullable=True)
