"""add_weekly_reports_table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-12 13:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "weekly_reports",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("week_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("week_end", sa.DateTime(timezone=True), nullable=False),
        # ScoutBot metrics
        sa.Column("leads_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("leads_published", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("enterprise_leads", sa.Integer(), nullable=False, server_default="0"),
        # ContentBot metrics
        sa.Column("content_generated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content_published", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content_cost_cents", sa.Integer(), nullable=False, server_default="0"),
        # CommunityBot metrics
        sa.Column("messages_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("messages_auto_resolved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("messages_escalated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("community_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resolution_rate", sa.Float(), nullable=False, server_default="0"),
        # AI-generated insights
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("action_items", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("weekly_reports")
