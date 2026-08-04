"""Workbench, Runs, and presenter tests for F-004."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from streamlit.testing.v1 import AppTest

from multi_agentic_graph_rag.domain.enums import RunStatus, TargetStage
from multi_agentic_graph_rag.domain.identifiers import new_uuid7
from multi_agentic_graph_rag.domain.schemas.commands import WorkflowRequest
from multi_agentic_graph_rag.domain.schemas.sources import SourcePath
from multi_agentic_graph_rag.ui.presenters.workflow_presenter import (
    latest_event,
    mermaid_diagram,
    stage_views,
    states_table,
)
from multi_agentic_graph_rag.workflows.events import (
    WorkflowEvent,
    WorkflowNodeState,
    WorkflowRunSnapshot,
    WorkflowStage,
    WorkflowStageState,
)


def test_workflow_presenter_renders_canonical_stage_order() -> None:
    """The workflow presenter keeps labels and state rows in canonical order."""
    run = _run_snapshot()

    views = stage_views(run)
    assert [view.label for view in views][:3] == [
        "Validate request",
        "Ingest",
        "Discover requirements",
    ]
    assert "Validate request" in mermaid_diagram(run)
    assert states_table(run)[0] == {"Stage": "Validate request", "State": "SUCCEEDED"}
    assert latest_event(run).activity == "Validated."


def test_workbench_render_shows_truthful_status_shell() -> None:
    """The Workbench shell renders the command surface without claiming execution."""
    app = AppTest.from_string(
        """
from multi_agentic_graph_rag.bootstrap import build_app_context
from multi_agentic_graph_rag.ui.pages.workbench import render
render(build_app_context())
"""
    ).run(timeout=10)

    assert not app.exception
    assert app.title[0].value == "Workbench"
    assert any(item.value == "Workflow" for item in app.subheader)
    assert any(item.value == "Execution status" for item in app.subheader)
    assert any(item.value == "Conversation" for item in app.subheader)


def test_runs_render_shows_empty_state_and_filters() -> None:
    """The Runs page renders its presentation shell and truthful empty state."""
    app = AppTest.from_string(
        """
from multi_agentic_graph_rag.ui.pages.runs import render
render()
"""
    ).run(timeout=10)

    assert not app.exception
    assert app.title[0].value == "Runs"
    assert any(
        item.value == "No workflow runs are available for the current filters." for item in app.info
    )


def test_runs_render_lists_session_run_rows() -> None:
    """A recorded run appears in the Runs view with sanitized status text."""
    script = """
import streamlit as st
from datetime import UTC, datetime
from multi_agentic_graph_rag.domain.enums import RunStatus, TargetStage
from multi_agentic_graph_rag.domain.identifiers import new_uuid7
from multi_agentic_graph_rag.domain.schemas.commands import WorkflowRequest
from multi_agentic_graph_rag.domain.schemas.sources import SourcePath
from multi_agentic_graph_rag.ui.pages.runs import render
from multi_agentic_graph_rag.ui.state.session import append_workflow_run
from multi_agentic_graph_rag.workflows.events import WorkflowEvent, WorkflowNodeState, WorkflowRunSnapshot, WorkflowStage, WorkflowStageState
from pathlib import Path
document_root = Path("documents/inbox").resolve()
document_root.mkdir(parents=True, exist_ok=True)
source_file = document_root / "brief.pdf"
source_file.write_text("document body", encoding="utf-8")
source = SourcePath(original_text="brief.pdf", document_root=document_root, resolved_path=source_file, extension=".pdf", size_bytes=source_file.stat().st_size)
request = WorkflowRequest(project_id=new_uuid7(), run_id=new_uuid7(), source=source, target_stage=TargetStage.REQUIREMENTS)
timestamp = datetime(2026, 8, 4, 12, 30, tzinfo=UTC)
event = WorkflowEvent(project_id=request.project_id, run_id=request.run_id, stage=WorkflowStage.VALIDATE_REQUEST, state=WorkflowNodeState.SUCCEEDED, timestamp=timestamp, activity="Validated.")
run = WorkflowRunSnapshot(request=request, status=RunStatus.BLOCKED, created_at=timestamp, updated_at=timestamp, events=(event,), stage_states=(WorkflowStageState(stage=WorkflowStage.VALIDATE_REQUEST, state=WorkflowNodeState.SUCCEEDED),))
append_workflow_run(run)
render()
"""
    app = AppTest.from_string(script).run(timeout=10)

    assert not app.exception
    assert app.title[0].value == "Runs"
    assert len(app.table) == 1
    assert app.table[0].value["Status"].iat[0] == "BLOCKED"


def _run_snapshot() -> WorkflowRunSnapshot:
    document_root = _document_root()
    source_file = document_root / "brief.pdf"
    source_file.write_text("document body", encoding="utf-8")
    request = WorkflowRequest(
        project_id=new_uuid7(),
        run_id=new_uuid7(),
        source=SourcePath(
            original_text="brief.pdf",
            document_root=document_root,
            resolved_path=source_file,
            extension=".pdf",
            size_bytes=source_file.stat().st_size,
        ),
        target_stage=TargetStage.USER_STORIES,
    )
    timestamp = datetime(2026, 8, 4, 12, 30, tzinfo=UTC)
    event = WorkflowEvent(
        project_id=request.project_id,
        run_id=request.run_id,
        stage=WorkflowStage.VALIDATE_REQUEST,
        state=WorkflowNodeState.SUCCEEDED,
        timestamp=timestamp,
        activity="Validated.",
    )
    return WorkflowRunSnapshot(
        request=request,
        status=RunStatus.BLOCKED,
        created_at=timestamp,
        updated_at=timestamp,
        events=(event,),
        stage_states=(
            WorkflowStageState(
                stage=WorkflowStage.VALIDATE_REQUEST, state=WorkflowNodeState.SUCCEEDED
            ),
            WorkflowStageState(stage=WorkflowStage.INGEST, state=WorkflowNodeState.BLOCKED),
            WorkflowStageState(
                stage=WorkflowStage.DISCOVER_REQUIREMENTS, state=WorkflowNodeState.PENDING
            ),
            WorkflowStageState(stage=WorkflowStage.RETRIEVE, state=WorkflowNodeState.PENDING),
            WorkflowStageState(
                stage=WorkflowStage.GENERATE_STORIES, state=WorkflowNodeState.PENDING
            ),
            WorkflowStageState(
                stage=WorkflowStage.GENERATE_SCENARIOS, state=WorkflowNodeState.SKIPPED
            ),
            WorkflowStageState(stage=WorkflowStage.COVERAGE, state=WorkflowNodeState.SKIPPED),
        ),
    )


def _document_root():
    document_root = Path("documents/inbox").resolve()
    document_root.mkdir(parents=True, exist_ok=True)
    return document_root
