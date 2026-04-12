"""add_content_table

Revision ID: a1b2c3d4e5f6
Revises: e258e7a8ea74
Create Date: 2026-04-12 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "e258e7a8ea74"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contents",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "content_type",
            sa.Enum(
                "seo_article",
                "industry_brief",
                "tutorial",
                "comparison",
                "changelog",
                "social_post",
                name="contenttype",
            ),
            nullable=False,
        ),
        sa.Column(
            "language",
            sa.Enum("en", "zh", name="contentlanguage"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "draft",
                "review",
                "approved",
                "scheduled",
                "published",
                "rejected",
                name="contentstatus",
            ),
            nullable=False,
        ),
        sa.Column("seo_keyword", sa.String(length=255), nullable=True),
        sa.Column("seo_tags", sa.Text(), nullable=True),
        sa.Column("outline_model", sa.String(length=100), nullable=True),
        sa.Column("body_model", sa.String(length=100), nullable=True),
        sa.Column("translate_model", sa.String(length=100), nullable=True),
        sa.Column("generation_cost_cents", sa.Integer(), nullable=False),
        sa.Column("target_platform", sa.String(length=50), nullable=False),
        sa.Column("published_url", sa.Text(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality_passed", sa.Boolean(), nullable=False),
        sa.Column("quality_notes", sa.Text(), nullable=True),
        sa.Column("pair_id", sa.String(length=50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("contents")
    op.execute("DROP TYPE IF EXISTS contenttype")
    op.execute("DROP TYPE IF EXISTS contentlanguage")
    op.execute("DROP TYPE IF EXISTS contentstatus")
