"""Neo4j rebuildable projection-scope adapter."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from neo4j import Driver, GraphDatabase
from neo4j.exceptions import AuthError, ConfigurationError, Neo4jError, ServiceUnavailable

from multi_agentic_graph_rag.config.settings import (
    PersistenceCredentials,
    PersistenceSettings,
)
from multi_agentic_graph_rag.domain.errors import (
    NotFoundError,
    StorePermanentError,
    StoreTransientError,
)
from multi_agentic_graph_rag.domain.identifiers import UUID7
from multi_agentic_graph_rag.domain.schemas.artifacts import CanonicalChunks, EmbeddingFingerprint
from multi_agentic_graph_rag.domain.schemas.runs import ProjectionScope
from multi_agentic_graph_rag.ports.repositories import StoreHealth


class Neo4jProjectionRepository:
    """Persist only rebuildable project projection metadata in Neo4j."""

    def __init__(
        self,
        settings: PersistenceSettings,
        credentials: PersistenceCredentials,
    ) -> None:
        self._settings = settings
        self._password = credentials.neo4j_password

    def ensure_scope(self, scope: ProjectionScope) -> ProjectionScope:
        """Create the projection-scope constraint and upsert one project scope."""
        with self._driver() as driver, driver.session(database="neo4j") as session:
            session.run(
                """
                CREATE CONSTRAINT projection_scope_project IF NOT EXISTS
                FOR (scope:ProjectionScope) REQUIRE scope.project_id IS UNIQUE
                """
            ).consume()
            record = session.run(
                """
                MERGE (scope:ProjectionScope {project_id: $project_id})
                SET scope.schema_version = $schema_version,
                    scope.source_checksum = $source_checksum
                RETURN scope.schema_version AS schema_version,
                       scope.source_checksum AS source_checksum
                """,
                project_id=str(scope.project_id),
                schema_version=scope.schema_version,
                source_checksum=scope.source_checksum,
            ).single(strict=True)
        return ProjectionScope(
            schema_version=record["schema_version"],
            project_id=scope.project_id,
            source_checksum=record["source_checksum"],
        )

    def get_scope(self, *, project_id: UUID7) -> ProjectionScope:
        """Read one Neo4j projection scope by explicit project ID."""
        with self._driver() as driver, driver.session(database="neo4j") as session:
            record = session.run(
                """
                MATCH (scope:ProjectionScope {project_id: $project_id})
                RETURN scope.schema_version AS schema_version,
                       scope.source_checksum AS source_checksum
                """,
                project_id=str(project_id),
            ).single()
        if record is None:
            raise NotFoundError("Neo4j projection scope was not found.")
        return ProjectionScope(
            schema_version=record["schema_version"],
            project_id=project_id,
            source_checksum=record["source_checksum"],
        )

    def upsert_chunks(
        self,
        *,
        chunks: CanonicalChunks,
        embeddings: tuple[tuple[float, ...], ...],
        fingerprint: EmbeddingFingerprint,
    ) -> None:
        """Idempotently create project-scoped Chunk nodes."""
        if len(chunks.chunks) != len(embeddings):
            raise ValueError("Chunk and embedding counts must match.")
        rows = [
            {
                "project_id": str(chunk.project_id),
                "run_id": str(chunk.run_id),
                "source_id": str(chunk.source_id),
                "chunk_id": str(chunk.chunk_id),
                "ordinal": chunk.ordinal,
                "text": chunk.text,
                "text_checksum": chunk.text_checksum,
                "embedding_fingerprint": fingerprint.fingerprint,
                "embedding_dimension": fingerprint.dimension,
            }
            for chunk in chunks.chunks
        ]
        with self._driver() as driver, driver.session(database="neo4j") as session:
            session.run(
                """
                UNWIND $rows AS row
                MERGE (chunk:Chunk {
                    project_id: row.project_id,
                    chunk_id: row.chunk_id
                })
                SET chunk.run_id = row.run_id,
                    chunk.source_id = row.source_id,
                    chunk.ordinal = row.ordinal,
                    chunk.text = row.text,
                    chunk.text_checksum = row.text_checksum,
                    chunk.embedding_fingerprint = row.embedding_fingerprint,
                    chunk.embedding_dimension = row.embedding_dimension
                """,
                rows=rows,
            ).consume()

    def read_chunk_ids(
        self, *, project_id: UUID7, chunk_ids: tuple[UUID7, ...]
    ) -> tuple[UUID7, ...]:
        """Read back only requested chunk IDs within one project."""
        with self._driver() as driver, driver.session(database="neo4j") as session:
            records = session.run(
                """
                MATCH (chunk:Chunk {project_id: $project_id})
                WHERE chunk.chunk_id IN $chunk_ids
                RETURN chunk.chunk_id AS chunk_id
                ORDER BY chunk.ordinal
                """,
                project_id=str(project_id),
                chunk_ids=[str(chunk_id) for chunk_id in chunk_ids],
            )
            return tuple(UUID(record["chunk_id"]) for record in records)

    def check_health(self) -> StoreHealth:
        """Run a bounded authenticated Neo4j connectivity probe."""
        if self._password is None:
            return StoreHealth("Neo4j", False, "Store credential is required")
        try:
            with self._driver() as driver:
                driver.verify_connectivity()
        except (StorePermanentError, StoreTransientError):
            return StoreHealth("Neo4j", False, "Store connection failed")
        return StoreHealth("Neo4j", True, "Ready")

    @contextmanager
    def _driver(self) -> Iterator[Driver]:
        if self._password is None:
            raise StorePermanentError("Neo4j credential is required.")
        try:
            with GraphDatabase.driver(
                self._settings.neo4j_uri,
                auth=(self._settings.neo4j_user, self._password.get_secret_value()),
                connection_timeout=float(self._settings.health_timeout_seconds),
                connection_acquisition_timeout=float(self._settings.health_timeout_seconds),
            ) as driver:
                yield driver
        except ServiceUnavailable as error:
            raise StoreTransientError("Neo4j is unavailable.") from error
        except (AuthError, ConfigurationError, Neo4jError) as error:
            raise StorePermanentError("Neo4j connection failed.") from error
