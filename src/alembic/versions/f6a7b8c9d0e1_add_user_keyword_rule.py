"""add user_keyword_rule table

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index('ix_user_keyword_rule_pattern', table_name='user_keyword_rule')
    op.drop_table('user_keyword_rule')
