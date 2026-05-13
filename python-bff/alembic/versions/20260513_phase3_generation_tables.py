"""phase 3 generation tables

Revision ID: 20260513_phase3_generation_tables
Revises: 003_data_layer
Create Date: 2026-05-13 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260513_phase3_generation_tables"
down_revision: Union[str, None] = "003_data_layer"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "generation_assets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("asset_role", sa.String(length=32), nullable=False, server_default="source"),
        sa.Column("oss_bucket", sa.String(length=128), nullable=False),
        sa.Column("oss_key", sa.String(length=1024), nullable=False),
        sa.Column("original_filename", sa.String(length=256), nullable=False, server_default=""),
        sa.Column("content_type", sa.String(length=128), nullable=False, server_default="application/octet-stream"),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("etag", sa.String(length=128), nullable=False, server_default=""),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "oss_key", name="uq_generation_assets_tenant_oss_key"),
    )
    op.create_index("ix_generation_assets_tenant_id", "generation_assets", ["tenant_id"], unique=False)
    op.create_index("ix_generation_assets_job_id", "generation_assets", ["job_id"], unique=False)

    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("client_request_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("category_id", sa.Uuid(), nullable=True),
        sa.Column("style_id", sa.Uuid(), nullable=True),
        sa.Column("source_asset_id", sa.Uuid(), nullable=False),
        sa.Column("raw_result_asset_id", sa.Uuid(), nullable=True),
        sa.Column("watermarked_result_asset_id", sa.Uuid(), nullable=True),
        sa.Column("task_id", sa.String(length=128), nullable=True),
        sa.Column("provider", sa.String(length=64), nullable=False, server_default="wanxiang"),
        sa.Column("model_name", sa.String(length=64), nullable=False, server_default="wan2.7-image"),
        sa.Column("rule_snapshot", sa.JSON(), nullable=False),
        sa.Column("prompt_snapshot", sa.JSON(), nullable=False),
        sa.Column("request_snapshot", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("error_message", sa.String(length=1024), nullable=False, server_default=""),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
        sa.ForeignKeyConstraint(["style_id"], ["styles.id"]),
        sa.ForeignKeyConstraint(["source_asset_id"], ["generation_assets.id"]),
        sa.ForeignKeyConstraint(["raw_result_asset_id"], ["generation_assets.id"]),
        sa.ForeignKeyConstraint(["watermarked_result_asset_id"], ["generation_assets.id"]),
        sa.UniqueConstraint("tenant_id", "client_request_id", name="uq_generation_jobs_tenant_client_request_id"),
    )
    op.create_index("ix_generation_jobs_tenant_id", "generation_jobs", ["tenant_id"], unique=False)
    op.create_index("ix_generation_jobs_status", "generation_jobs", ["status"], unique=False)
    op.create_index("ix_generation_jobs_category_id", "generation_jobs", ["category_id"], unique=False)
    op.create_index("ix_generation_jobs_style_id", "generation_jobs", ["style_id"], unique=False)
    op.create_index("ix_generation_jobs_source_asset_id", "generation_jobs", ["source_asset_id"], unique=False)
    op.create_index("ix_generation_jobs_raw_result_asset_id", "generation_jobs", ["raw_result_asset_id"], unique=False)
    op.create_index(
        "ix_generation_jobs_watermarked_result_asset_id",
        "generation_jobs",
        ["watermarked_result_asset_id"],
        unique=False,
    )
    op.create_index("ix_generation_jobs_task_id", "generation_jobs", ["task_id"], unique=True)

    op.create_table(
        "generation_job_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("message", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["job_id"], ["generation_jobs.id"]),
    )
    op.create_index("ix_generation_job_events_tenant_id", "generation_job_events", ["tenant_id"], unique=False)
    op.create_index("ix_generation_job_events_job_id", "generation_job_events", ["job_id"], unique=False)
    op.create_index("ix_generation_job_events_event_type", "generation_job_events", ["event_type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_generation_job_events_event_type", table_name="generation_job_events")
    op.drop_index("ix_generation_job_events_job_id", table_name="generation_job_events")
    op.drop_index("ix_generation_job_events_tenant_id", table_name="generation_job_events")
    op.drop_table("generation_job_events")

    op.drop_index("ix_generation_jobs_task_id", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_watermarked_result_asset_id", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_raw_result_asset_id", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_source_asset_id", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_style_id", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_category_id", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_status", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_tenant_id", table_name="generation_jobs")
    op.drop_table("generation_jobs")

    op.drop_index("ix_generation_assets_job_id", table_name="generation_assets")
    op.drop_index("ix_generation_assets_tenant_id", table_name="generation_assets")
    op.drop_table("generation_assets")
