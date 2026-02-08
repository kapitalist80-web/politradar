"""widen decision column in votings table to varchar(100)

Revision ID: 003_widen_decision
Revises: 002_widen_abbr
Create Date: 2026-02-08
"""

from alembic import op
import sqlalchemy as sa

revision = "003_widen_decision"
down_revision = "002_widen_abbr"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("votings", "decision",
                    type_=sa.String(100), existing_type=sa.String(20))


def downgrade() -> None:
    op.alter_column("votings", "decision",
                    type_=sa.String(20), existing_type=sa.String(100))
