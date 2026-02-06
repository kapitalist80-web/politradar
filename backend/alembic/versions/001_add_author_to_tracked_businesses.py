"""add author and submitted_text columns to tracked_businesses

Revision ID: 001
Revises:
Create Date: 2026-02-06
"""

from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tracked_businesses", sa.Column("author", sa.String(500), nullable=True))
    op.add_column("tracked_businesses", sa.Column("submitted_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("tracked_businesses", "submitted_text")
    op.drop_column("tracked_businesses", "author")
