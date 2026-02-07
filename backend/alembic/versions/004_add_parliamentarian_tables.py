"""add parliamentarian, committee, vote, prediction tables

Revision ID: 004
Revises: 003
Create Date: 2026-02-07
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cantons
    op.create_table(
        "cantons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canton_number", sa.Integer(), unique=True, nullable=False),
        sa.Column("canton_name", sa.String(100)),
        sa.Column("canton_abbreviation", sa.String(5)),
    )

    # Parties
    op.create_table(
        "parties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("party_number", sa.Integer(), unique=True, nullable=False),
        sa.Column("party_name", sa.String(255)),
        sa.Column("party_abbreviation", sa.String(20)),
        sa.Column("program_summary", sa.Text()),
        sa.Column("political_position", JSONB()),
        sa.Column("last_sync", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Parliamentary Groups
    op.create_table(
        "parl_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("parl_group_number", sa.Integer(), unique=True, nullable=False),
        sa.Column("parl_group_name", sa.String(255)),
        sa.Column("parl_group_abbreviation", sa.String(20)),
        sa.Column("associated_parties", sa.Text()),
        sa.Column("last_sync", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Parliamentarians
    op.create_table(
        "parliamentarians",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_number", sa.Integer(), unique=True, nullable=False),
        sa.Column("first_name", sa.String(255)),
        sa.Column("last_name", sa.String(255)),
        sa.Column("gender", sa.String(10)),
        sa.Column("date_of_birth", sa.Date()),
        sa.Column("canton_id", sa.Integer()),
        sa.Column("canton_name", sa.String(100)),
        sa.Column("canton_abbreviation", sa.String(5)),
        sa.Column("council_id", sa.Integer()),
        sa.Column("council_name", sa.String(100)),
        sa.Column("party_id", sa.Integer()),
        sa.Column("party_name", sa.String(255)),
        sa.Column("party_abbreviation", sa.String(20)),
        sa.Column("parl_group_id", sa.Integer()),
        sa.Column("parl_group_name", sa.String(255)),
        sa.Column("parl_group_abbreviation", sa.String(20)),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("membership_start", sa.Date()),
        sa.Column("membership_end", sa.Date()),
        sa.Column("biografie_url", sa.String(500)),
        sa.Column("photo_url", sa.String(500)),
        sa.Column("last_sync", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Committees
    op.create_table(
        "committees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("committee_number", sa.Integer(), unique=True, nullable=False),
        sa.Column("committee_name", sa.String(500)),
        sa.Column("committee_abbreviation", sa.String(20)),
        sa.Column("council_id", sa.Integer()),
        sa.Column("committee_type", sa.String(100)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("last_sync", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Committee Memberships
    op.create_table(
        "committee_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_number", sa.Integer(), nullable=False),
        sa.Column("committee_id", sa.Integer(), nullable=False),
        sa.Column("committee_name", sa.String(500)),
        sa.Column("committee_abbreviation", sa.String(20)),
        sa.Column("council_id", sa.Integer()),
        sa.Column("function", sa.String(100)),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("last_sync", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("person_number", "committee_id", "start_date", name="uq_committee_membership"),
    )

    # Votes
    op.create_table(
        "votes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vote_id", sa.Integer(), unique=True, nullable=False),
        sa.Column("business_number", sa.String(20)),
        sa.Column("business_title", sa.String(500)),
        sa.Column("subject", sa.Text()),
        sa.Column("meaning_yes", sa.Text()),
        sa.Column("meaning_no", sa.Text()),
        sa.Column("vote_date", sa.DateTime()),
        sa.Column("council_id", sa.Integer()),
        sa.Column("session_id", sa.String(50)),
        sa.Column("total_yes", sa.Integer()),
        sa.Column("total_no", sa.Integer()),
        sa.Column("total_abstain", sa.Integer()),
        sa.Column("total_not_voted", sa.Integer()),
        sa.Column("result", sa.String(50)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Votings (individual votes)
    op.create_table(
        "votings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vote_id", sa.Integer(), nullable=False),
        sa.Column("person_number", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(20), nullable=False),
        sa.Column("parl_group_number", sa.Integer()),
        sa.Column("canton_id", sa.Integer()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("vote_id", "person_number", name="uq_voting"),
    )
    op.create_index("idx_votings_person", "votings", ["person_number"])
    op.create_index("idx_votings_vote", "votings", ["vote_id"])
    op.create_index("idx_votings_decision", "votings", ["decision"])

    # Vote Predictions
    op.create_table(
        "vote_predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_number", sa.String(20), nullable=False),
        sa.Column("person_number", sa.Integer(), nullable=False),
        sa.Column("predicted_yes", sa.Float()),
        sa.Column("predicted_no", sa.Float()),
        sa.Column("predicted_abstain", sa.Float()),
        sa.Column("confidence", sa.Float()),
        sa.Column("model_version", sa.String(50)),
        sa.Column("prediction_date", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("business_number", "person_number", "model_version", name="uq_vote_prediction"),
    )


def downgrade() -> None:
    op.drop_table("vote_predictions")
    op.drop_index("idx_votings_decision", "votings")
    op.drop_index("idx_votings_vote", "votings")
    op.drop_index("idx_votings_person", "votings")
    op.drop_table("votings")
    op.drop_table("votes")
    op.drop_table("committee_memberships")
    op.drop_table("committees")
    op.drop_table("parliamentarians")
    op.drop_table("parl_groups")
    op.drop_table("parties")
    op.drop_table("cantons")
