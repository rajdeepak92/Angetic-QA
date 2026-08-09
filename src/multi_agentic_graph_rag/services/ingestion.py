"""Stage 1.1a deterministic ingestion use case."""

from __future__ import annotations

from datetime import datetime

from multi_agentic_graph_rag.domain.enums import RunStatus
from multi_agentic_graph_rag.domain.schemas.artifacts import CanonicalChunks
from multi_agentic_graph_rag.domain.schemas.commands import WorkflowRequest
from multi_agentic_graph_rag.domain.schemas.runs import ProjectRecord, RunRecord
from multi_agentic_graph_rag.domain.schemas.sources import SourceLedger
from multi_agentic_graph_rag.ports.documents import DocumentReaderPort
from multi_agentic_graph_rag.ports.repositories import RunRepositoryPort
from multi_agentic_graph_rag.services.chunking import build_chunks, build_source_ledger
from multi_agentic_graph_rag.services.parsing import parse_document


def ingest_document(
    request: WorkflowRequest,
    *,
    repository: RunRepositoryPort,
    reader: DocumentReaderPort,
    created_at: datetime,
) -> tuple[SourceLedger, CanonicalChunks]:
    """Parse, ledger, chunk, and persist one validated document."""
    content = request.source.resolved_path.read_bytes()
    repository.save_project(
        ProjectRecord(
            project_id=request.project_id, name=str(request.project_id), created_at=created_at
        )
    )
    repository.save_run(
        RunRecord(
            project_id=request.project_id,
            run_id=request.run_id,
            target_stage=request.target_stage,
            status=RunStatus.RUNNING,
            created_at=created_at,
            updated_at=created_at,
        )
    )
    blocks = parse_document(content, extension=request.source.extension, reader=reader)
    ledger = build_source_ledger(
        project_id=request.project_id,
        run_id=request.run_id,
        source_path=str(request.source.resolved_path),
        extension=request.source.extension,
        content=content,
        blocks=blocks,
    )
    chunks = build_chunks(ledger=ledger, blocks=blocks)
    repository.save_source_ledger(ledger)
    repository.save_chunks(chunks)
    return ledger, chunks
