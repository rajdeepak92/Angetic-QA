"""Strict workflow command and request contracts."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from multi_agentic_graph_rag.domain.enums import TargetStage
from multi_agentic_graph_rag.domain.identifiers import UUID7
from multi_agentic_graph_rag.domain.schemas.sources import SourcePath

COMMAND_MODEL_CONFIG = ConfigDict(
    strict=True,
    extra="forbid",
    frozen=True,
    validate_default=True,
)


class ParsedCommand(BaseModel):
    """Deterministic command-parser output before filesystem validation."""

    model_config = COMMAND_MODEL_CONFIG

    target_stage: TargetStage
    source_text: str


class WorkflowRequest(BaseModel):
    """Validated request accepted by the workflow boundary."""

    model_config = COMMAND_MODEL_CONFIG

    project_id: UUID7
    run_id: UUID7
    source: SourcePath
    target_stage: TargetStage
