from __future__ import annotations

from sqlalchemy import UniqueConstraint

from app.models import Base


def test_generation_models_registered():
    assert "generation_assets" in Base.metadata.tables
    assert "generation_jobs" in Base.metadata.tables
    assert "generation_job_events" in Base.metadata.tables


def test_generation_jobs_have_tenant_request_unique_constraint():
    table = Base.metadata.tables["generation_jobs"]
    unique_names = {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert "uq_generation_jobs_tenant_client_request_id" in unique_names
