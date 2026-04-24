"""add case lifecycle timestamps for MTTR/MTTA

Revision ID: 001_case_lifecycle
Revises:
Create Date: 2026-04-24

Adds acknowledged_at, resolved_at, closed_at columns to the `cases` table
so MTTA (time-to-acknowledge) and MTTR (time-to-resolve) can be measured.
Nullable — old cases won't have these stamped retroactively.
"""
from alembic import op
import sqlalchemy as sa


revision = "001_case_lifecycle"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cases",
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cases",
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cases",
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("cases", "closed_at")
    op.drop_column("cases", "resolved_at")
    op.drop_column("cases", "acknowledged_at")
