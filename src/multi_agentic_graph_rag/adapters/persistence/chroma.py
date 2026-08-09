"""Embedded Chroma rebuildable projection-scope adapter."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from chromadb import PersistentClient
from chromadb.api import ClientAPI
from chromadb.config import Settings
from chromadb.errors import ChromaError
from chromadb.errors import NotFoundError as ChromaNotFoundError

from multi_agentic_graph_rag.config.settings import PersistenceSettings
from multi_agentic_graph_rag.domain.errors import (
    DataIntegrityError,
    NotFoundError,
    StorePermanentError,
)
from multi_agentic_graph_rag.domain.identifiers import UUID7
from multi_agentic_graph_rag.domain.schemas.artifacts import CanonicalChunks, EmbeddingFingerprint
from multi_agentic_graph_rag.domain.schemas.runs import ProjectionScope
from multi_agentic_graph_rag.ports.repositories import StoreHealth


class ChromaProjectionRepository:
    """Persist one isolated embedded Chroma collection scope per project."""

    def __init__(self, settings: PersistenceSettings) -> None:
        self._path = settings.chroma_path

    def ensure_scope(self, scope: ProjectionScope) -> ProjectionScope:
        """Create or refresh one project collection's rebuild metadata."""
        try:
            collection: Any = self._client().get_or_create_collection(
                name=_collection_name(scope.project_id),
                metadata=_metadata(scope),
            )
            if collection.metadata != _metadata(scope):
                collection.modify(metadata=_metadata(scope))
            return self.get_scope(project_id=scope.project_id)
        except (OSError, ChromaError) as error:
            raise StorePermanentError("Chroma projection operation failed.") from error

    def get_scope(self, *, project_id: UUID7) -> ProjectionScope:
        """Read one isolated collection's projection metadata."""
        try:
            metadata = self._client().get_collection(_collection_name(project_id)).metadata or {}
        except ChromaNotFoundError as error:
            raise NotFoundError("Chroma projection scope was not found.") from error
        except (OSError, ChromaError) as error:
            raise StorePermanentError("Chroma projection operation failed.") from error
        return ProjectionScope(
            schema_version=_integer(metadata.get("schema_version")),
            project_id=project_id,
            source_checksum=_text(metadata.get("source_checksum")),
        )

    def upsert_chunks(
        self,
        *,
        chunks: CanonicalChunks,
        embeddings: tuple[tuple[float, ...], ...],
        fingerprint: EmbeddingFingerprint,
    ) -> None:
        """Idempotently upsert embeddings with project and fingerprint metadata."""
        if len(chunks.chunks) != len(embeddings):
            raise ValueError("Chunk and embedding counts must match.")
        try:
            collection: Any = self._client().get_or_create_collection(
                name=_collection_name(chunks.project_id),
                metadata={
                    "project_id": str(chunks.project_id),
                    "embedding_fingerprint": fingerprint.fingerprint,
                    "embedding_dimension": fingerprint.dimension,
                },
            )
            metadata = collection.metadata or {}
            if metadata.get("project_id") != str(chunks.project_id):
                raise DataIntegrityError("Chroma project boundary is inconsistent.")
            if metadata.get("embedding_fingerprint") not in {None, fingerprint.fingerprint}:
                raise DataIntegrityError("Chroma embedding fingerprint does not match.")
            if metadata.get("embedding_dimension") not in {None, fingerprint.dimension}:
                raise DataIntegrityError("Chroma embedding dimension does not match.")
            collection.modify(
                metadata={
                    **metadata,
                    "project_id": str(chunks.project_id),
                    "embedding_fingerprint": fingerprint.fingerprint,
                    "embedding_dimension": fingerprint.dimension,
                }
            )
            collection.upsert(
                ids=[str(chunk.chunk_id) for chunk in chunks.chunks],
                embeddings=[list(vector) for vector in embeddings],
                documents=[chunk.text for chunk in chunks.chunks],
                metadatas=[
                    {
                        "project_id": str(chunk.project_id),
                        "run_id": str(chunk.run_id),
                        "source_id": str(chunk.source_id),
                        "ordinal": chunk.ordinal,
                        "embedding_fingerprint": fingerprint.fingerprint,
                    }
                    for chunk in chunks.chunks
                ],
            )
        except DataIntegrityError:
            raise
        except (OSError, ChromaError) as error:
            raise StorePermanentError("Chroma projection operation failed.") from error

    def read_chunk_ids(
        self, *, project_id: UUID7, chunk_ids: tuple[UUID7, ...]
    ) -> tuple[UUID7, ...]:
        """Read back requested IDs from the normalized project collection."""
        try:
            result: Any = (
                self._client()
                .get_collection(_collection_name(project_id))
                .get(ids=[str(chunk_id) for chunk_id in chunk_ids], include=["metadatas"])
            )
            ids = result.get("ids", [])
            metadatas = result.get("metadatas", [])
            for metadata in metadatas:
                if metadata is not None and metadata.get("project_id") != str(project_id):
                    raise DataIntegrityError("Chroma readback crossed project boundaries.")
            return tuple(UUID(value) for value in ids)
        except (DataIntegrityError, NotFoundError):
            raise
        except ChromaNotFoundError as error:
            raise NotFoundError("Chroma chunk collection was not found.") from error
        except (OSError, ChromaError) as error:
            raise StorePermanentError("Chroma projection operation failed.") from error

    def check_health(self) -> StoreHealth:
        """Verify the local persistent client and filesystem readback."""
        try:
            self._path.mkdir(parents=True, exist_ok=True)
            is_ready = self._client().heartbeat() > 0
        except (OSError, ChromaError):
            return StoreHealth("Chroma", False, "Local persistence check failed")
        return StoreHealth("Chroma", is_ready, "Ready" if is_ready else "Readback failed")

    def _client(self) -> ClientAPI:
        return PersistentClient(
            path=str(self._path),
            settings=Settings(anonymized_telemetry=False, allow_reset=False),
        )


def _collection_name(project_id: UUID7) -> str:
    return f"magr_{project_id.hex}"


def _metadata(scope: ProjectionScope) -> dict[str, str | int]:
    return {
        "schema_version": scope.schema_version,
        "project_id": str(scope.project_id),
        "source_checksum": scope.source_checksum,
    }


def _integer(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise DataIntegrityError("Chroma returned invalid projection metadata.")
    return value


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise DataIntegrityError("Chroma returned invalid projection metadata.")
    return value
