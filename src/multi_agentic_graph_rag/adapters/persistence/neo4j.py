"""Neo4j rebuildable projection-scope adapter."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

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
