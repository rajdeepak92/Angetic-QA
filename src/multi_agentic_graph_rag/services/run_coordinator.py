"""Truthful F-004/F-006 run coordination through the completed ingest boundary."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from uuid import UUID

from multi_agentic_graph_rag.config.settings import AppSettings, CredentialBundle
from multi_agentic_graph_rag.domain.enums import RunStatus, TargetStage
from multi_agentic_graph_rag.domain.identifiers import UUID7, new_uuid7
from multi_agentic_graph_rag.domain.schemas.commands import WorkflowRequest
from multi_agentic_graph_rag.ports.documents import DocumentReaderPort
from multi_agentic_graph_rag.ports.models import EmbeddingModelPort
from multi_agentic_graph_rag.ports.repositories import ChunkProjectionPort, RunRepositoryPort
from multi_agentic_graph_rag.services.command_parser import parse_chat_command
from multi_agentic_graph_rag.services.ingestion import ingest_document
from multi_agentic_graph_rag.services.path_policy import validate_document_path
from multi_agentic_graph_rag.services.projection import project_chunks
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
        repository: RunRepositoryPort | None = None,
        readers: Mapping[str, DocumentReaderPort] | None = None,
        embedding_model_factory: Callable[[AppSettings, CredentialBundle], EmbeddingModelPort]
        | None = None,
        neo4j: ChunkProjectionPort | None = None,
        chroma: ChunkProjectionPort | None = None,
    ) -> None:
        self._clock = clock or _utc_now
        self._id_factory = id_factory
        self._repository = repository
        self._readers = readers or {}
        self._embedding_model_factory = embedding_model_factory
        self._neo4j = neo4j
        self._chroma = chroma

    def submit(
        self,
        command_text: str,
        *,
        project_id: UUID7,
        settings: AppSettings,
        credentials: CredentialBundle | None = None,
    ) -> WorkflowRunSnapshot:
        """Validate one chat command and execute the wired ingest boundary truthfully."""
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
        validation_event = WorkflowEvent(
            project_id=project_id,
            run_id=run_id,
            stage=WorkflowStage.VALIDATE_REQUEST,
            state=WorkflowNodeState.SUCCEEDED,
            timestamp=created_at,
            activity="Request and source path validated.",
            item_count=1,
        )
        if (
            self._repository is None
            or request.source.extension not in self._readers
            or self._embedding_model_factory is None
            or self._neo4j is None
            or self._chroma is None
            or credentials is None
        ):
            blocked_events = (
                validation_event,
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
                events=blocked_events,
                stage_states=_stage_states(request.target_stage),
            )

        _, chunks = ingest_document(
            request,
            repository=self._repository,
            reader=self._readers[request.source.extension],
            created_at=created_at,
        )
        manifest = project_chunks(
            chunks,
            embedding_model=self._embedding_model_factory(settings, credentials),
            neo4j=self._neo4j,
            chroma=self._chroma,
            generated_root=settings.generated_root,
        )
        events: tuple[WorkflowEvent, ...] = (
            validation_event,
            WorkflowEvent(
                project_id=project_id,
                run_id=run_id,
                stage=WorkflowStage.INGEST,
                state=WorkflowNodeState.SUCCEEDED,
                timestamp=created_at,
                activity="Document parsed and canonical chunks persisted.",
                item_count=len(chunks.chunks),
            ),
            WorkflowEvent(
                project_id=project_id,
                run_id=run_id,
                stage=WorkflowStage.INGEST,
                state=WorkflowNodeState.SUCCEEDED,
                timestamp=created_at,
                activity="Chunks embedded, projected to Neo4j and Chroma, and manifest written.",
                item_count=len(manifest.chunks),
            ),
        )
        return WorkflowRunSnapshot(
            request=request,
            status=RunStatus.RUNNING,
            created_at=created_at,
            updated_at=created_at,
            events=events,
            stage_states=_stage_states(
                request.target_stage, ingest_state=WorkflowNodeState.SUCCEEDED
            ),
        )


def _stage_states(
    target_stage: TargetStage,
    *,
    ingest_state: WorkflowNodeState = WorkflowNodeState.BLOCKED,
) -> tuple[WorkflowStageState, ...]:
    requested = set(TARGET_STAGE_WORKFLOW[target_stage])
    states = {
        stage: (WorkflowNodeState.PENDING if stage in requested else WorkflowNodeState.SKIPPED)
        for stage in WORKFLOW_STAGES
    }
    states[WorkflowStage.VALIDATE_REQUEST] = WorkflowNodeState.SUCCEEDED
    states[WorkflowStage.INGEST] = ingest_state
    return tuple(WorkflowStageState(stage=stage, state=states[stage]) for stage in WORKFLOW_STAGES)


def _utc_now() -> datetime:
    return datetime.now(UTC)
