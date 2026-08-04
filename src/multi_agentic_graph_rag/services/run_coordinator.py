"""Truthful F-004 run coordination without executing later workflow stages."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from multi_agentic_graph_rag.config.settings import AppSettings
from multi_agentic_graph_rag.domain.enums import RunStatus, TargetStage
from multi_agentic_graph_rag.domain.identifiers import UUID7, new_uuid7
from multi_agentic_graph_rag.domain.schemas.commands import WorkflowRequest
from multi_agentic_graph_rag.services.command_parser import parse_chat_command
from multi_agentic_graph_rag.services.path_policy import validate_document_path
from multi_agentic_graph_rag.workflows.events import (
    TARGET_STAGE_WORKFLOW,
    WORKFLOW_STAGES,
    WorkflowEvent,
    WorkflowNodeState,
    WorkflowRunSnapshot,
    WorkflowStage,
    WorkflowStageState,
)

F005_BLOCKER = "Document ingestion is not implemented until F-005."


class RunCoordinator:
    """Create typed requests and emit only real validation/blocking events."""

    def __init__(
        self,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], UUID] = new_uuid7,
    ) -> None:
        self._clock = clock or _utc_now
        self._id_factory = id_factory

    def submit(
        self,
        command_text: str,
        *,
        project_id: UUID7,
        settings: AppSettings,
    ) -> WorkflowRunSnapshot:
        """Validate one chat command and return a truthful non-executed run snapshot."""
        parsed = parse_chat_command(command_text)
        run_id = self._id_factory()
        source = validate_document_path(parsed.source_text, document_root=settings.document_root)
        request = WorkflowRequest(
            project_id=project_id,
            run_id=run_id,
            source=source,
            target_stage=parsed.target_stage,
        )
        created_at = self._clock()
        events = (
            WorkflowEvent(
                project_id=project_id,
                run_id=run_id,
                stage=WorkflowStage.VALIDATE_REQUEST,
                state=WorkflowNodeState.SUCCEEDED,
                timestamp=created_at,
                activity="Request and source path validated.",
                item_count=1,
            ),
            WorkflowEvent(
                project_id=project_id,
                run_id=run_id,
                stage=WorkflowStage.INGEST,
                state=WorkflowNodeState.BLOCKED,
                timestamp=created_at,
                activity="Execution paused before document ingestion.",
                error_summary=F005_BLOCKER,
            ),
        )
        return WorkflowRunSnapshot(
            request=request,
            status=RunStatus.BLOCKED,
            created_at=created_at,
            updated_at=created_at,
            events=events,
            stage_states=_stage_states(request.target_stage),
        )


def _stage_states(target_stage: TargetStage) -> tuple[WorkflowStageState, ...]:
    requested = set(TARGET_STAGE_WORKFLOW[target_stage])
    states = {
        stage: (WorkflowNodeState.PENDING if stage in requested else WorkflowNodeState.SKIPPED)
        for stage in WORKFLOW_STAGES
    }
    states[WorkflowStage.VALIDATE_REQUEST] = WorkflowNodeState.SUCCEEDED
    states[WorkflowStage.INGEST] = WorkflowNodeState.BLOCKED
    return tuple(WorkflowStageState(stage=stage, state=states[stage]) for stage in WORKFLOW_STAGES)


def _utc_now() -> datetime:
    return datetime.now(UTC)
