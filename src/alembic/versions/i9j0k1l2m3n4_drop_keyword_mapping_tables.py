"""drop keyword_mapping and user_keyword_rule tables

Revision ID: i9j0k1l2m3n4
Revises: h8i9j0k1l2m3
Create Date: 2026-04-21 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'i9j0k1l2m3n4'
down_revision: Union[str, Sequence[str], None] = 'h8i9j0k1l2m3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index('ix_user_keyword_rule_pattern', table_name='user_keyword_rule')
    op.drop_table('user_keyword_rule')
    op.drop_index('ix_keyword_mapping_raw_keyword', table_name='keyword_mapping')
    op.drop_index('ix_keyword_mapping_canonical_keyword', table_name='keyword_mapping')
    op.drop_table('keyword_mapping')


def downgrade() -> None:
    op.create_table(
        'keyword_mapping',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_keyword', sa.Text(), nullable=False),
        sa.Column('canonical_keyword', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('raw_keyword', 'canonical_keyword', 'user_id', name='uq_mapping_per_user'),
    )
    op.create_index('ix_keyword_mapping_raw_keyword', 'keyword_mapping', ['raw_keyword'])
    op.create_index('ix_keyword_mapping_canonical_keyword', 'keyword_mapping', ['canonical_keyword'])
    op.create_table(
        'user_keyword_rule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pattern', sa.Text(), nullable=False),
        sa.Column('keyword', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('case_sensitive', sa.Boolean(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('pattern', 'user_id', name='uq_rule_per_user'),
    )
    op.create_index('ix_user_keyword_rule_pattern', 'user_keyword_rule', ['pattern'])
