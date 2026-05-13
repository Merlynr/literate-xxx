"""phase 4 quota billing

Revision ID: 20260513_phase4_qb
Revises: 20260513_phase3_gen
Create Date: 2026-05-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260513_phase4_qb"
down_revision = "20260513_phase3_gen"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pricing_plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("plan_code", sa.String(length=64), nullable=False),
        sa.Column("plan_name", sa.String(length=128), nullable=False),
        sa.Column("quota_units", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("plan_code", name="uq_pricing_plans_plan_code"),
    )
    op.create_index("ix_pricing_plans_is_active", "pricing_plans", ["is_active"])
    op.create_index("ix_pricing_plans_sort_order", "pricing_plans", ["sort_order"])

    op.create_table(
        "quota_accounts",
        sa.Column("id", sa.CHAR(length=32), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.CHAR(length=32), nullable=False),
        sa.Column("total_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("frozen_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active_plan_id", sa.Integer(), sa.ForeignKey("pricing_plans.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("tenant_id", name="uq_quota_accounts_tenant_id"),
    )
    op.create_index("ix_quota_accounts_tenant_id", "quota_accounts", ["tenant_id"])
    op.create_index("ix_quota_accounts_active_plan_id", "quota_accounts", ["active_plan_id"])

    op.create_table(
        "quota_ledger_entries",
        sa.Column("id", sa.CHAR(length=32), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.CHAR(length=32), nullable=False),
        sa.Column("job_id", sa.CHAR(length=32), nullable=True),
        sa.Column("plan_id", sa.Integer(), sa.ForeignKey("pricing_plans.id"), nullable=True),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("delta_units", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_before", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_after", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("frozen_before", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("frozen_after", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reason", sa.String(length=256), nullable=False, server_default=""),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_quota_ledger_entries_tenant_id", "quota_ledger_entries", ["tenant_id"])
    op.create_index("ix_quota_ledger_entries_job_id", "quota_ledger_entries", ["job_id"])
    op.create_index("ix_quota_ledger_entries_event_type", "quota_ledger_entries", ["event_type"])

    op.create_table(
        "user_consents",
        sa.Column("id", sa.CHAR(length=32), primary_key=True, nullable=False),
        sa.Column("tenant_id", sa.CHAR(length=32), nullable=False),
        sa.Column("user_id", sa.CHAR(length=32), nullable=False),
        sa.Column("consent_type", sa.String(length=64), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="generation"),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("tenant_id", "user_id", "consent_type", name="uq_user_consents_tenant_user_type"),
    )
    op.create_index("ix_user_consents_tenant_id", "user_consents", ["tenant_id"])
    op.create_index("ix_user_consents_user_id", "user_consents", ["user_id"])
    op.create_index("ix_user_consents_consent_type", "user_consents", ["consent_type"])

    op.bulk_insert(
        sa.table(
            "pricing_plans",
            sa.column("plan_code", sa.String),
            sa.column("plan_name", sa.String),
            sa.column("quota_units", sa.Integer),
            sa.column("price_cents", sa.Integer),
            sa.column("valid_days", sa.Integer),
            sa.column("is_active", sa.Boolean),
            sa.column("sort_order", sa.Integer),
        ),
        [
            {
                "plan_code": "DEFAULT_100",
                "plan_name": "Default 100",
                "quota_units": 100,
                "price_cents": 0,
                "valid_days": 30,
                "is_active": True,
                "sort_order": 0,
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("user_consents")
    op.drop_table("quota_ledger_entries")
    op.drop_table("quota_accounts")
    op.drop_index("ix_pricing_plans_sort_order", table_name="pricing_plans")
    op.drop_index("ix_pricing_plans_is_active", table_name="pricing_plans")
    op.drop_table("pricing_plans")
