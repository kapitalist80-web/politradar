"""Add priority, business_notes table, and session_name to votes

Revision ID: 006
Revises: 005
Create Date: 2026-02-11
"""

from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add priority column to tracked_businesses
    op.add_column("tracked_businesses", sa.Column("priority", sa.Integer(), nullable=True))

    # Add session_name column to votes
    op.add_column("votes", sa.Column("session_name", sa.String(200), nullable=True))

    # Create business_notes table
    op.create_table(
        "business_notes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "business_id",
            sa.Integer(),
            sa.ForeignKey("tracked_businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_business_notes_business", "business_notes", ["business_id"])


def downgrade() -> None:
    op.drop_table("business_notes")
    op.drop_column("votes", "session_name")
    op.drop_column("tracked_businesses", "priority")
