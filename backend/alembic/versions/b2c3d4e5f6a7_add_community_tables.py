"""add_community_tables

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-12 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("source_file", sa.String(length=500), nullable=False),
        sa.Column("heading", sa.String(length=500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "community_messages",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("channel_id", sa.String(length=100), nullable=False),
        sa.Column("author_id", sa.String(length=100), nullable=False),
        sa.Column("author_name", sa.String(length=255), nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=50), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("escalated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_lead", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("community_messages")
    op.drop_table("knowledge_chunks")
