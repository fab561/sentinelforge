"""add evidence table for case attachments

Revision ID: 002_evidence
Revises: 001_case_lifecycle
Create Date: 2026-04-24

Stores file metadata for case attachments (PCAPs, Cowrie session logs,
screenshots, etc). The bytes live in MinIO keyed by sha256; this table
only tracks pointers + metadata for listing and access control.
"""
from alembic import op
import sqlalchemy as sa


revision = "002_evidence"
down_revision = "001_case_lifecycle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "case_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=30), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False, index=True),
        sa.Column("storage_key", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "uploaded_by",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_evidence_case_id", "evidence", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_case_id", table_name="evidence")
    op.drop_table("evidence")
