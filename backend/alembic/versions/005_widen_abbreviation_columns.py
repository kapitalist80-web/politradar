"""widen abbreviation columns from varchar(20) to varchar(50)

Revision ID: 005
Revises: 004
Create Date: 2026-02-07
"""

from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("parties", "party_abbreviation",
                    type_=sa.String(50), existing_type=sa.String(20))
    op.alter_column("parl_groups", "parl_group_abbreviation",
                    type_=sa.String(50), existing_type=sa.String(20))
    op.alter_column("parliamentarians", "party_abbreviation",
                    type_=sa.String(50), existing_type=sa.String(20))
    op.alter_column("parliamentarians", "parl_group_abbreviation",
                    type_=sa.String(50), existing_type=sa.String(20))
    op.alter_column("committees", "committee_abbreviation",
                    type_=sa.String(50), existing_type=sa.String(20))
    op.alter_column("committee_memberships", "committee_abbreviation",
                    type_=sa.String(50), existing_type=sa.String(20))


def downgrade() -> None:
    op.alter_column("committee_memberships", "committee_abbreviation",
                    type_=sa.String(20), existing_type=sa.String(50))
    op.alter_column("committees", "committee_abbreviation",
                    type_=sa.String(20), existing_type=sa.String(50))
    op.alter_column("parliamentarians", "parl_group_abbreviation",
                    type_=sa.String(20), existing_type=sa.String(50))
    op.alter_column("parliamentarians", "party_abbreviation",
                    type_=sa.String(20), existing_type=sa.String(50))
    op.alter_column("parl_groups", "parl_group_abbreviation",
                    type_=sa.String(20), existing_type=sa.String(50))
    op.alter_column("parties", "party_abbreviation",
                    type_=sa.String(20), existing_type=sa.String(50))
