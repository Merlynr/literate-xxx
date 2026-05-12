"""data layer - categories, styles, terms, promo_rules

Revision ID: 003_data_layer
Revises: 002_auth_tables
Create Date: 2026-05-12 20:10:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

revision: str = "003_data_layer"
down_revision: Union[str, None] = "002_auth_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create categories table
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("category_code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_tenant_id", "categories", ["tenant_id"], unique=False)
    op.create_index("ix_categories_category_code", "categories", ["category_code"], unique=True)

    # Create styles table
    op.create_table(
        "styles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("cover_image_url", sa.String(length=512), nullable=False, server_default=""),
        sa.Column("rule_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_styles_tenant_id", "styles", ["tenant_id"], unique=False)

    # Create terms table
    op.create_table(
        "terms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("content", sa.String(length=512), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("scope", mysql.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_terms_tenant_id", "terms", ["tenant_id"], unique=False)

    # Create promo_rules table
    op.create_table(
        "promo_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("slot_template", mysql.JSON(), nullable=True),
        sa.Column("term_selection_strategy", sa.String(length=64), nullable=False, server_default="weighted_random"),
        sa.Column("aspect_ratio", sa.String(length=16), nullable=False, server_default="1:1"),
        sa.Column("watermark_config", mysql.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_promo_rules_tenant_id", "promo_rules", ["tenant_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_promo_rules_tenant_id", table_name="promo_rules")
    op.drop_table("promo_rules")
    op.drop_index("ix_terms_tenant_id", table_name="terms")
    op.drop_table("terms")
    op.drop_index("ix_styles_tenant_id", table_name="styles")
    op.drop_table("styles")
    op.drop_index("ix_categories_category_code", table_name="categories")
    op.drop_index("ix_categories_tenant_id", table_name="categories")
    op.drop_table("categories")
