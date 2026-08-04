"""Embedded Chroma rebuildable projection-scope adapter."""

from __future__ import annotations

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
from multi_agentic_graph_rag.domain.schemas.runs import ProjectionScope
from multi_agentic_graph_rag.ports.repositories import StoreHealth


class ChromaProjectionRepository:
    """Persist one isolated embedded Chroma collection scope per project."""

    def __init__(self, settings: PersistenceSettings) -> None:
        self._path = settings.chroma_path

    def ensure_scope(self, scope: ProjectionScope) -> ProjectionScope:
        """Create or refresh one project collection's rebuild metadata."""
        try:
            collection = self._client().get_or_create_collection(
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
