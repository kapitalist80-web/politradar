"""widen committee_abbreviation columns to varchar(255)

Revision ID: 002_widen_abbr
Revises: 001_initial
Create Date: 2026-02-08
"""

from alembic import op
import sqlalchemy as sa

revision = "002_widen_abbr"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("committees", "committee_abbreviation",
                    type_=sa.String(255), existing_type=sa.String(50))
    op.alter_column("committee_memberships", "committee_abbreviation",
                    type_=sa.String(255), existing_type=sa.String(50))


def downgrade() -> None:
    op.alter_column("committee_memberships", "committee_abbreviation",
                    type_=sa.String(50), existing_type=sa.String(255))
    op.alter_column("committees", "committee_abbreviation",
                    type_=sa.String(50), existing_type=sa.String(255))
