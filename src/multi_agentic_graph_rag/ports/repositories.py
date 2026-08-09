"""Typed ports for canonical and rebuildable persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from multi_agentic_graph_rag.domain.identifiers import UUID7
from multi_agentic_graph_rag.domain.schemas.artifacts import CanonicalChunks, EmbeddingFingerprint
from multi_agentic_graph_rag.domain.schemas.runs import ProjectionScope, ProjectRecord, RunRecord
from multi_agentic_graph_rag.domain.schemas.sources import SourceLedger


@dataclass(frozen=True, slots=True)
class StoreHealth:
    """Sanitized bounded store-health result."""

    name: str
    is_ready: bool
    detail: str


class PersistenceHealthPort(Protocol):
    """Report readiness without exposing credentials or vendor errors."""

    def check_health(self) -> StoreHealth:
        """Return one sanitized health result."""
        ...


class RunRepositoryPort(PersistenceHealthPort, Protocol):
    """Canonical PostgreSQL project and run persistence."""

    def initialize_schema(self) -> None:
        """Apply every pending immutable migration idempotently."""
        ...

    def save_project(self, project: ProjectRecord) -> None:
        """Persist a canonical project."""
        ...

    def save_run(self, run: RunRecord) -> None:
        """Persist current canonical state for one project-scoped run."""
        ...

    def get_run(self, *, project_id: UUID7, run_id: UUID7) -> RunRecord:
        """Read one run only within its explicit project boundary."""
        ...

    def save_source_ledger(self, ledger: SourceLedger) -> None:
        """Persist one source ledger within its project/run scope."""
        ...

    def save_chunks(self, chunks: CanonicalChunks) -> None:
        """Persist one ordered canonical chunk set within its source scope."""
        ...


class ProjectionScopePort(PersistenceHealthPort, Protocol):
    """Persist rebuildable project projection metadata."""

    def ensure_scope(self, scope: ProjectionScope) -> ProjectionScope:
        """Idempotently create or refresh one project projection scope."""
        ...


class ChunkProjectionPort(Protocol):
    """Store and verify one project-scoped chunk projection."""

    def upsert_chunks(
        self,
        *,
        chunks: CanonicalChunks,
        embeddings: tuple[tuple[float, ...], ...],
        fingerprint: EmbeddingFingerprint,
    ) -> None:
        """Idempotently write canonical chunks and their embeddings."""
        ...

    def read_chunk_ids(
        self, *, project_id: UUID7, chunk_ids: tuple[UUID7, ...]
    ) -> tuple[UUID7, ...]:
        """Read back chunk IDs within the explicit project boundary."""
        ...

    def get_scope(self, *, project_id: UUID7) -> ProjectionScope:
        """Read projection metadata for one explicit project."""
        ...
