"""Workflow event and request contract tests."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from multi_agentic_graph_rag.domain.enums import RunStatus, TargetStage
from multi_agentic_graph_rag.domain.identifiers import new_uuid7
from multi_agentic_graph_rag.domain.schemas.commands import WorkflowRequest
from multi_agentic_graph_rag.domain.schemas.sources import SourcePath
from multi_agentic_graph_rag.workflows.events import (
    WorkflowEvent,
    WorkflowNodeState,
    WorkflowRunSnapshot,
    WorkflowStage,
    WorkflowStageState,
)


def test_workflow_request_rejects_extra_fields() -> None:
    """Workflow requests stay strict at the typed boundary."""
    source = _source_path()

    with pytest.raises(ValidationError, match="Extra inputs"):
        WorkflowRequest(
            project_id=new_uuid7(),
            run_id=new_uuid7(),
            source=source,
            target_stage=TargetStage.USER_STORIES,
            unexpected=True,
        )


def test_workflow_event_rejects_naive_timestamps_and_snapshot_is_strict() -> None:
    """Workflow events and snapshots require aware timestamps and typed state."""
    source = _source_path()
    request = WorkflowRequest(
        project_id=new_uuid7(),
        run_id=new_uuid7(),
        source=source,
        target_stage=TargetStage.USER_STORIES,
    )
    aware = datetime(2026, 8, 4, 12, 30, tzinfo=UTC)

    with pytest.raises(ValidationError, match="timezone-aware"):
        WorkflowEvent(
            project_id=request.project_id,
            run_id=request.run_id,
            stage=WorkflowStage.VALIDATE_REQUEST,
            state=WorkflowNodeState.SUCCEEDED,
            timestamp=aware.replace(tzinfo=None),
            activity="Validated.",
        )

    event = WorkflowEvent(
        project_id=request.project_id,
        run_id=request.run_id,
        stage=WorkflowStage.VALIDATE_REQUEST,
        state=WorkflowNodeState.SUCCEEDED,
        timestamp=aware,
        activity="Validated.",
    )
    snapshot = WorkflowRunSnapshot(
        request=request,
        status=RunStatus.BLOCKED,
        created_at=aware,
        updated_at=aware,
        events=(event,),
        stage_states=(
            WorkflowStageState(
                stage=WorkflowStage.VALIDATE_REQUEST, state=WorkflowNodeState.SUCCEEDED
            ),
        ),
    )

    assert snapshot.events[0].activity == "Validated."


def _source_path() -> SourcePath:
    document_root = Path("documents/inbox").resolve()
    document_root.mkdir(parents=True, exist_ok=True)
    resolved = document_root / "brief.pdf"
    resolved.write_text("document body", encoding="utf-8")
    return SourcePath(
        original_text="brief.pdf",
        document_root=document_root,
        resolved_path=resolved,
        extension=".pdf",
        size_bytes=resolved.stat().st_size,
    )
