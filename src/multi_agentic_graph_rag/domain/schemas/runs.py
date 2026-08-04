"""Strict project, run, and projection-scope contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from multi_agentic_graph_rag.domain.enums import ErrorCategory, RunStatus, TargetStage
from multi_agentic_graph_rag.domain.identifiers import UUID7, Checksum

DOMAIN_MODEL_CONFIG = ConfigDict(
    strict=True,
    extra="forbid",
    frozen=True,
    validate_default=True,
)


class ProjectRecord(BaseModel):
    """Canonical project boundary persisted by PostgreSQL."""

    model_config = DOMAIN_MODEL_CONFIG

    schema_version: int = Field(default=1, ge=1)
    project_id: UUID7
    name: str = Field(min_length=1, max_length=200)
    created_at: datetime

    @field_validator("name")
    @classmethod
    def reject_ambiguous_name(cls, value: str) -> str:
        """Reject project names with surrounding whitespace."""
        if value != value.strip():
            raise ValueError("Project name must not contain surrounding whitespace.")
        return value

    @field_validator("created_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        """Require persisted timestamps to carry an offset."""
        return _aware(value)


class RunFailure(BaseModel):
    """Sanitized classified failure persisted with a failed run."""

    model_config = DOMAIN_MODEL_CONFIG

    category: ErrorCategory
    message: str = Field(min_length=1, max_length=500)


class RunRecord(BaseModel):
    """Canonical project-scoped workflow run state."""

    model_config = DOMAIN_MODEL_CONFIG

    schema_version: int = Field(default=1, ge=1)
    project_id: UUID7
    run_id: UUID7
    target_stage: TargetStage
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    failure: RunFailure | None = None

    @field_validator("created_at", "updated_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        """Require persisted timestamps to carry an offset."""
        return _aware(value)

    @model_validator(mode="after")
    def validate_state(self) -> RunRecord:
        """Keep timestamps and terminal failure state consistent."""
        if self.updated_at < self.created_at:
            raise ValueError("Run update time cannot precede creation time.")
        if (self.status is RunStatus.FAILED) != (self.failure is not None):
            raise ValueError("Only failed runs must contain a failure.")
        return self


class ProjectionScope(BaseModel):
    """Rebuildable project projection metadata shared by Neo4j and Chroma."""

    model_config = DOMAIN_MODEL_CONFIG

    schema_version: int = Field(default=1, ge=1)
    project_id: UUID7
    source_checksum: Checksum


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Persisted timestamps must be timezone-aware.")
    return value
