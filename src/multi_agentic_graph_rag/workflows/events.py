"""Typed workflow event and presentation-state contracts."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from multi_agentic_graph_rag.domain.enums import RunStatus, TargetStage
from multi_agentic_graph_rag.domain.identifiers import UUID7
from multi_agentic_graph_rag.domain.schemas.commands import WorkflowRequest

WORKFLOW_MODEL_CONFIG = ConfigDict(
    strict=True,
    extra="forbid",
    frozen=True,
    validate_default=True,
)


class WorkflowStage(StrEnum):
    """Stable UI-visible workflow stages."""

    VALIDATE_REQUEST = "validate_request"
    INGEST = "ingest"
    DISCOVER_REQUIREMENTS = "discover_requirements"
    RETRIEVE = "retrieve"
    GENERATE_STORIES = "generate_stories"
    GENERATE_SCENARIOS = "generate_scenarios"
    COVERAGE = "coverage"

    @property
    def label(self) -> str:
        """Return the accessible stage label shown in the UI."""
        return {
            WorkflowStage.VALIDATE_REQUEST: "Validate request",
            WorkflowStage.INGEST: "Ingest",
            WorkflowStage.DISCOVER_REQUIREMENTS: "Discover requirements",
            WorkflowStage.RETRIEVE: "Retrieve",
            WorkflowStage.GENERATE_STORIES: "Generate stories",
            WorkflowStage.GENERATE_SCENARIOS: "Generate scenarios",
            WorkflowStage.COVERAGE: "Coverage",
        }[self]


class WorkflowNodeState(StrEnum):
    """Allowed workflow node presentation states."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


WORKFLOW_STAGES: tuple[WorkflowStage, ...] = (
    WorkflowStage.VALIDATE_REQUEST,
    WorkflowStage.INGEST,
    WorkflowStage.DISCOVER_REQUIREMENTS,
    WorkflowStage.RETRIEVE,
    WorkflowStage.GENERATE_STORIES,
    WorkflowStage.GENERATE_SCENARIOS,
    WorkflowStage.COVERAGE,
)

TARGET_STAGE_WORKFLOW: dict[TargetStage, tuple[WorkflowStage, ...]] = {
    TargetStage.REQUIREMENTS: (
        WorkflowStage.VALIDATE_REQUEST,
        WorkflowStage.INGEST,
        WorkflowStage.DISCOVER_REQUIREMENTS,
    ),
    TargetStage.USER_STORIES: (
        WorkflowStage.VALIDATE_REQUEST,
        WorkflowStage.INGEST,
        WorkflowStage.DISCOVER_REQUIREMENTS,
        WorkflowStage.RETRIEVE,
        WorkflowStage.GENERATE_STORIES,
    ),
    TargetStage.TEST_SCENARIOS: WORKFLOW_STAGES,
}


class WorkflowEvent(BaseModel):
    """One sanitized workflow event safe for UI presentation."""

    model_config = WORKFLOW_MODEL_CONFIG

    project_id: UUID7
    run_id: UUID7
    stage: WorkflowStage
    state: WorkflowNodeState
    timestamp: datetime
    activity: str = Field(min_length=1, max_length=300)
    attempt: int = Field(default=1, ge=1)
    item_count: int = Field(default=0, ge=0)
    duration_ms: int = Field(default=0, ge=0)
    error_summary: str | None = Field(default=None, min_length=1, max_length=500)

    @field_validator("timestamp")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        """Require UI event timestamps to carry an offset."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Workflow event timestamps must be timezone-aware.")
        return value


class WorkflowStageState(BaseModel):
    """Current display state for one workflow stage."""

    model_config = WORKFLOW_MODEL_CONFIG

    stage: WorkflowStage
    state: WorkflowNodeState


class WorkflowRunSnapshot(BaseModel):
    """Session-visible run state derived from real request validation events."""

    model_config = WORKFLOW_MODEL_CONFIG

    request: WorkflowRequest
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    events: tuple[WorkflowEvent, ...]
    stage_states: tuple[WorkflowStageState, ...]

    @field_validator("created_at", "updated_at")
    @classmethod
    def require_aware_time(cls, value: datetime) -> datetime:
        """Require run timestamps to carry an offset."""
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("Workflow run timestamps must be timezone-aware.")
        return value
