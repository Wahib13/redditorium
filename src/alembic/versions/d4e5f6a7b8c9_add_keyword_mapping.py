"""add keyword_mapping table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'keyword_mapping',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_keyword', sa.Text(), nullable=False),
        sa.Column('canonical_keyword', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('raw_keyword', 'canonical_keyword', 'user_id', name='uq_mapping_per_user'),
    )
    op.create_index('ix_keyword_mapping_raw_keyword', 'keyword_mapping', ['raw_keyword'])
    op.create_index('ix_keyword_mapping_canonical_keyword', 'keyword_mapping', ['canonical_keyword'])


def downgrade() -> None:
    op.drop_index('ix_keyword_mapping_canonical_keyword', table_name='keyword_mapping')
    op.drop_index('ix_keyword_mapping_raw_keyword', table_name='keyword_mapping')
    op.drop_table('keyword_mapping')
