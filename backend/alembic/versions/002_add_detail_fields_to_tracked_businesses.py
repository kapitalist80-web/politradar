"""add reasoning, federal_council_response, federal_council_proposal, first_council

Revision ID: 002
Revises: 001
Create Date: 2026-02-06
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tracked_businesses", sa.Column("reasoning", sa.Text(), nullable=True))
    op.add_column("tracked_businesses", sa.Column("federal_council_response", sa.Text(), nullable=True))
    op.add_column("tracked_businesses", sa.Column("federal_council_proposal", sa.String(200), nullable=True))
    op.add_column("tracked_businesses", sa.Column("first_council", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("tracked_businesses", "first_council")
    op.drop_column("tracked_businesses", "federal_council_proposal")
    op.drop_column("tracked_businesses", "federal_council_response")
    op.drop_column("tracked_businesses", "reasoning")
