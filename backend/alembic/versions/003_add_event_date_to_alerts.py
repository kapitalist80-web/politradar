"""add event_date column to alerts table

Revision ID: 003
Revises: 002
Create Date: 2026-02-07
"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("alerts", sa.Column("event_date", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("alerts", "event_date")
