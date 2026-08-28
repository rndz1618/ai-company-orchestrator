"""phase15 soft delete and pause types

Revision ID: a1b2c3d4e5f6
Revises: 8d5da4fc0b82
Create Date: 2026-08-28 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '8d5da4fc0b82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Soft-delete columns ---
    op.add_column('companies', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('agents', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('workflow_templates', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('tasks', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()))

    # --- AgentStatus enum expansion ---
    # SQLite does not support ALTER TYPE. Application-level enum values are sufficient.
    # For PostgreSQL, recreate the enum properly.
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("ALTER TYPE agentstatus RENAME TO agentstatus_old")
        op.execute("CREATE TYPE agentstatus AS ENUM ('ACTIVE', 'PAUSED_BUDGET', 'PAUSED_MANUAL', 'DISABLED')")
        op.execute("""
            ALTER TABLE agents
            ALTER COLUMN status TYPE agentstatus
            USING (
                CASE status::text
                    WHEN 'PAUSED' THEN 'PAUSED_BUDGET'::agentstatus
                    ELSE status::text::agentstatus
                END
            )
        """)
        op.execute("DROP TYPE agentstatus_old")


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("ALTER TYPE agentstatus RENAME TO agentstatus_new")
        op.execute("CREATE TYPE agentstatus AS ENUM ('ACTIVE', 'PAUSED', 'DISABLED')")
        op.execute("""
            ALTER TABLE agents
            ALTER COLUMN status TYPE agentstatus
            USING (
                CASE status::text
                    WHEN 'PAUSED_BUDGET' THEN 'PAUSED'::agentstatus
                    WHEN 'PAUSED_MANUAL' THEN 'PAUSED'::agentstatus
                    ELSE status::text::agentstatus
                END
            )
        """)
        op.execute("DROP TYPE agentstatus_new")

    op.drop_column('tasks', 'is_active')
    op.drop_column('workflow_templates', 'is_active')
    op.drop_column('agents', 'is_active')
    op.drop_column('companies', 'is_active')
