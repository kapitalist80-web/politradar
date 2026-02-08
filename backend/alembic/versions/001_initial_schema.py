"""initial schema - consolidated migration

Revision ID: 001_initial
Revises:
Create Date: 2026-02-08
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("email_alerts_enabled", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("email_alert_types", sa.String(500), server_default="status_change,committee_scheduled,debate_scheduled"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Tracked Businesses
    op.create_table(
        "tracked_businesses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("business_number", sa.String(20), nullable=False),
        sa.Column("title", sa.String(500)),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.String(100)),
        sa.Column("business_type", sa.String(100)),
        sa.Column("author", sa.String(500)),
        sa.Column("author_faction", sa.String(255)),
        sa.Column("submitted_text", sa.Text()),
        sa.Column("reasoning", sa.Text()),
        sa.Column("federal_council_response", sa.Text()),
        sa.Column("federal_council_proposal", sa.String(200)),
        sa.Column("first_council", sa.String(100)),
        sa.Column("submission_date", sa.DateTime()),
        sa.Column("last_api_sync", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_tracked_businesses_id", "tracked_businesses", ["id"])
    op.create_index("ix_tracked_businesses_business_number", "tracked_businesses", ["business_number"])

    # Business Events
    op.create_table(
        "business_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_number", sa.String(20), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("event_date", sa.DateTime()),
        sa.Column("description", sa.Text()),
        sa.Column("committee_name", sa.String(255)),
        sa.Column("raw_data", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_business_events_id", "business_events", ["id"])
    op.create_index("ix_business_events_business_number", "business_events", ["business_number"])

    # Alerts
    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("business_number", sa.String(20), nullable=False),
        sa.Column(
            "alert_type",
            sa.Enum(
                "status_change",
                "committee_scheduled",
                "debate_scheduled",
                "new_document",
                "vote_result",
                name="alert_type_enum",
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("event_date", sa.DateTime()),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_id", "alerts", ["id"])

    # Monitoring Candidates
    op.create_table(
        "monitoring_candidates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("business_number", sa.String(20), nullable=False, unique=True),
        sa.Column("title", sa.String(500)),
        sa.Column("description", sa.Text()),
        sa.Column("business_type", sa.String(100)),
        sa.Column("submission_date", sa.DateTime()),
        sa.Column(
            "decision",
            sa.Enum("pending", "accepted", "rejected", name="decision_enum"),
            server_default="pending",
        ),
        sa.Column("decided_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.Column("decided_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_monitoring_candidates_id", "monitoring_candidates", ["id"])

    # Cantons
    op.create_table(
        "cantons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canton_number", sa.Integer(), unique=True, nullable=False),
        sa.Column("canton_name", sa.String(100)),
        sa.Column("canton_abbreviation", sa.String(5)),
    )
    op.create_index("ix_cantons_id", "cantons", ["id"])

    # Parties
    op.create_table(
        "parties",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("party_number", sa.Integer(), unique=True, nullable=False),
        sa.Column("party_name", sa.String(255)),
        sa.Column("party_abbreviation", sa.String(50)),
        sa.Column("program_summary", sa.Text()),
        sa.Column("political_position", JSONB()),
        sa.Column("last_sync", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_parties_id", "parties", ["id"])

    # Parliamentary Groups
    op.create_table(
        "parl_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("parl_group_number", sa.Integer(), unique=True, nullable=False),
        sa.Column("parl_group_name", sa.String(255)),
        sa.Column("parl_group_abbreviation", sa.String(50)),
        sa.Column("associated_parties", sa.Text()),
        sa.Column("last_sync", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_parl_groups_id", "parl_groups", ["id"])

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
        sa.Column("party_abbreviation", sa.String(50)),
        sa.Column("parl_group_id", sa.Integer()),
        sa.Column("parl_group_name", sa.String(255)),
        sa.Column("parl_group_abbreviation", sa.String(50)),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("membership_start", sa.Date()),
        sa.Column("membership_end", sa.Date()),
        sa.Column("biografie_url", sa.String(500)),
        sa.Column("photo_url", sa.String(500)),
        sa.Column("last_sync", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_parliamentarians_id", "parliamentarians", ["id"])

    # Committees
    op.create_table(
        "committees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("committee_number", sa.Integer(), unique=True, nullable=False),
        sa.Column("committee_name", sa.String(500)),
        sa.Column("committee_abbreviation", sa.String(50)),
        sa.Column("council_id", sa.Integer()),
        sa.Column("committee_type", sa.String(100)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("last_sync", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index("ix_committees_id", "committees", ["id"])

    # Committee Memberships
    op.create_table(
        "committee_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_number", sa.Integer(), nullable=False),
        sa.Column("committee_id", sa.Integer(), nullable=False),
        sa.Column("committee_name", sa.String(500)),
        sa.Column("committee_abbreviation", sa.String(50)),
        sa.Column("council_id", sa.Integer()),
        sa.Column("function", sa.String(100)),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("last_sync", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("person_number", "committee_id", "start_date", name="uq_committee_membership"),
    )
    op.create_index("ix_committee_memberships_id", "committee_memberships", ["id"])

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
    op.create_index("ix_votes_id", "votes", ["id"])

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
    op.create_index("ix_votings_id", "votings", ["id"])
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
    op.create_index("ix_vote_predictions_id", "vote_predictions", ["id"])


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
    op.drop_table("monitoring_candidates")
    op.drop_table("alerts")
    op.drop_table("business_events")
    op.drop_table("tracked_businesses")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS decision_enum")
    op.execute("DROP TYPE IF EXISTS alert_type_enum")
