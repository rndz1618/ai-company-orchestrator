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

    # --- AgentStatus enum expansion (PostgreSQL only) ---
    # Python model uses lowercase values: active, paused_budget, paused_manual, disabled.
    # Initial migration used UPPERCASE names; align to lowercase .value from the str Enum.
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("ALTER TYPE agentstatus RENAME TO agentstatus_old")
        op.execute(
            "CREATE TYPE agentstatus AS ENUM "
            "('active', 'paused_budget', 'paused_manual', 'disabled')"
        )
        op.execute("""
            ALTER TABLE agents
            ALTER COLUMN status TYPE agentstatus
            USING (
                CASE lower(status::text)
                    WHEN 'paused' THEN 'paused_budget'::agentstatus
                    WHEN 'active' THEN 'active'::agentstatus
                    WHEN 'disabled' THEN 'disabled'::agentstatus
                    WHEN 'paused_budget' THEN 'paused_budget'::agentstatus
                    WHEN 'paused_manual' THEN 'paused_manual'::agentstatus
                    ELSE 'active'::agentstatus
                END
            )
        """)
        op.execute("DROP TYPE agentstatus_old")
    # SQLite: native enum not enforced; application-level values only


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("ALTER TYPE agentstatus RENAME TO agentstatus_new")
        op.execute("CREATE TYPE agentstatus AS ENUM ('ACTIVE', 'PAUSED', 'DISABLED')")
        op.execute("""
            ALTER TABLE agents
            ALTER COLUMN status TYPE agentstatus
            USING (
                CASE lower(status::text)
                    WHEN 'paused_budget' THEN 'PAUSED'::agentstatus
                    WHEN 'paused_manual' THEN 'PAUSED'::agentstatus
                    WHEN 'active' THEN 'ACTIVE'::agentstatus
                    WHEN 'disabled' THEN 'DISABLED'::agentstatus
                    ELSE 'ACTIVE'::agentstatus
                END
            )
        """)
        op.execute("DROP TYPE agentstatus_new")

    op.drop_column('tasks', 'is_active')
    op.drop_column('workflow_templates', 'is_active')
    op.drop_column('agents', 'is_active')
    op.drop_column('companies', 'is_active')
