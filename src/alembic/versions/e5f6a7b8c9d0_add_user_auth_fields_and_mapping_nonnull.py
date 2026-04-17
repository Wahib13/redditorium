"""add user auth fields and make keyword_mapping.user_id non-nullable

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('hashed_password', sa.String(), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('admin', sa.Boolean(), nullable=False, server_default='0'))

    # Drop any orphaned global mappings (user_id IS NULL) before making column non-nullable
    op.execute("DELETE FROM keyword_mapping WHERE user_id IS NULL")

    with op.batch_alter_table('keyword_mapping') as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table('keyword_mapping') as batch_op:
        batch_op.alter_column('user_id', existing_type=sa.Integer(), nullable=True)

    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('admin')
        batch_op.drop_column('hashed_password')
