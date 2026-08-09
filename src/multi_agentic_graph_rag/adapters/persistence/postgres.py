"""Canonical PostgreSQL project/run repository and migration runner."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import psycopg
from psycopg import Connection
from psycopg.types.json import Jsonb

from multi_agentic_graph_rag.config.settings import (
    PersistenceCredentials,
    PersistenceSettings,
)
from multi_agentic_graph_rag.domain.enums import ErrorCategory, RunStatus, TargetStage
from multi_agentic_graph_rag.domain.errors import (
    DataIntegrityError,
    NotFoundError,
    StorePermanentError,
    StoreTransientError,
)
from multi_agentic_graph_rag.domain.identifiers import UUID7, checksum_bytes
from multi_agentic_graph_rag.domain.schemas.artifacts import CanonicalChunks
from multi_agentic_graph_rag.domain.schemas.runs import (
    ProjectRecord,
    RunFailure,
    RunRecord,
)
from multi_agentic_graph_rag.domain.schemas.sources import SourceLedger
from multi_agentic_graph_rag.ports.repositories import StoreHealth

_MIGRATIONS = Path(__file__).with_name("migrations")


class PostgresRunRepository:
    """Persist canonical projects and runs through short transactions."""

    def __init__(
        self,
        settings: PersistenceSettings,
        credentials: PersistenceCredentials,
        migrations_path: Path = _MIGRATIONS,
    ) -> None:
        self._settings = settings
        self._password = credentials.postgres_password
        self._migrations_path = migrations_path

    def initialize_schema(self) -> None:
        """Apply ordered SQL migrations once and verify immutable checksums."""
        migrations = sorted(self._migrations_path.glob("[0-9][0-9][0-9][0-9]_*.sql"))
        if not migrations:
            raise DataIntegrityError("No PostgreSQL migrations are available.")
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(hashtext('agentic_qa_schema'))")
            cursor.execute("CREATE SCHEMA IF NOT EXISTS agentic_qa")
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agentic_qa.schema_migrations (
                    version integer PRIMARY KEY,
                    filename text NOT NULL UNIQUE,
                    checksum char(64) NOT NULL,
                    applied_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                "SELECT version, checksum FROM agentic_qa.schema_migrations ORDER BY version"
            )
            applied = {_integer(row[0]): _text(row[1]) for row in cursor.fetchall()}
            for migration in migrations:
                version = int(migration.name.split("_", 1)[0])
                sql = migration.read_text(encoding="utf-8").replace("\r\n", "\n")
                checksum = checksum_bytes(sql.encode("utf-8"))
                if version in applied:
                    if applied[version] != checksum:
                        raise DataIntegrityError("An applied PostgreSQL migration was modified.")
                    continue
                cursor.execute(sql)
                cursor.execute(
                    """
                    INSERT INTO agentic_qa.schema_migrations (version, filename, checksum)
                    VALUES (%s, %s, %s)
                    """,
                    (version, migration.name, checksum),
                )

    def save_project(self, project: ProjectRecord) -> None:
        """Insert or update one canonical project."""
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO agentic_qa.projects (
                    project_id, schema_version, name, created_at
                ) VALUES (%s, %s, %s, %s)
                ON CONFLICT (project_id) DO UPDATE SET
                    schema_version = EXCLUDED.schema_version,
                    name = EXCLUDED.name
                """,
                (
                    project.project_id,
                    project.schema_version,
                    project.name,
                    project.created_at,
                ),
            )

    def save_run(self, run: RunRecord) -> None:
        """Insert or update one run inside its canonical project."""
        category = run.failure.category.value if run.failure else None
        message = run.failure.message if run.failure else None
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO agentic_qa.runs (
                    project_id, run_id, schema_version, target_stage, status,
                    created_at, updated_at, error_category, error_message
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (project_id, run_id) DO UPDATE SET
                    schema_version = EXCLUDED.schema_version,
                    target_stage = EXCLUDED.target_stage,
                    status = EXCLUDED.status,
                    updated_at = EXCLUDED.updated_at,
                    error_category = EXCLUDED.error_category,
                    error_message = EXCLUDED.error_message
                """,
                (
                    run.project_id,
                    run.run_id,
                    run.schema_version,
                    run.target_stage.value,
                    run.status.value,
                    run.created_at,
                    run.updated_at,
                    category,
                    message,
                ),
            )

    def get_run(self, *, project_id: UUID7, run_id: UUID7) -> RunRecord:
        """Read one run without permitting an unscoped lookup."""
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT schema_version, target_stage, status, created_at, updated_at,
                       error_category, error_message
                FROM agentic_qa.runs
                WHERE project_id = %s AND run_id = %s
                """,
                (project_id, run_id),
            )
            row = cursor.fetchone()
        if row is None:
            raise NotFoundError("Run was not found in the requested project.")
        category = _optional_text(row[5])
        message = _optional_text(row[6])
        if (category is None) != (message is None):
            raise DataIntegrityError("PostgreSQL returned inconsistent run failure data.")
        failure = (
            RunFailure(category=ErrorCategory(category), message=message)
            if category is not None and message is not None
            else None
        )
        return RunRecord(
            schema_version=_integer(row[0]),
            project_id=project_id,
            run_id=run_id,
            target_stage=TargetStage(_text(row[1])),
            status=RunStatus(_text(row[2])),
            created_at=_datetime(row[3]),
            updated_at=_datetime(row[4]),
            failure=failure,
        )

    def save_source_ledger(self, ledger: SourceLedger) -> None:
        """Insert or replace one immutable source ledger in its run scope."""
        with self._connection() as connection, connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO agentic_qa.sources (
                    project_id, run_id, source_id, schema_version, source_path,
                    extension, byte_checksum, normalized_checksum, block_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (project_id, run_id, source_id) DO NOTHING
                """,
                (
                    ledger.project_id,
                    ledger.run_id,
                    ledger.source_id,
                    ledger.schema_version,
                    ledger.source_path,
                    ledger.extension,
                    ledger.byte_checksum,
                    ledger.normalized_checksum,
                    ledger.block_count,
                ),
            )

    def save_chunks(self, chunks: CanonicalChunks) -> None:
        """Insert one canonical ordered chunk set in a single transaction."""
        with self._connection() as connection, connection.cursor() as cursor:
            for chunk in chunks.chunks:
                cursor.execute(
                    """
                    INSERT INTO agentic_qa.chunks (
                        project_id, run_id, source_id, chunk_id, schema_version,
                        ordinal, text, text_checksum, provenance
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (project_id, run_id, chunk_id) DO NOTHING
                    """,
                    (
                        chunk.project_id,
                        chunk.run_id,
                        chunk.source_id,
                        chunk.chunk_id,
                        chunk.schema_version,
                        chunk.ordinal,
                        chunk.text,
                        chunk.text_checksum,
                        Jsonb(chunk.provenance.model_dump(mode="json")),
                    ),
                )

    def check_health(self) -> StoreHealth:
        """Run a bounded read-only PostgreSQL probe."""
        if self._password is None:
            return StoreHealth("PostgreSQL", False, "Store credential is required")
        try:
            with self._connection() as connection, connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                is_ready = cursor.fetchone() == (1,)
        except (StoreTransientError, StorePermanentError):
            return StoreHealth("PostgreSQL", False, "Store connection failed")
        return StoreHealth(
            "PostgreSQL",
            is_ready,
            "Ready" if is_ready else "Store readback failed",
        )

    @contextmanager
    def _connection(self) -> Iterator[Connection[tuple[object, ...]]]:
        if self._password is None:
            raise StorePermanentError("PostgreSQL credential is required.")
        try:
            with psycopg.connect(
                host=self._settings.postgres_host,
                port=self._settings.postgres_port,
                dbname=self._settings.postgres_database,
                user=self._settings.postgres_user,
                password=self._password.get_secret_value(),
                connect_timeout=self._settings.health_timeout_seconds,
                options=(f"-c statement_timeout={self._settings.health_timeout_seconds * 1000}"),
            ) as connection:
                yield connection
        except DataIntegrityError:
            raise
        except psycopg.OperationalError as error:
            raise StoreTransientError("PostgreSQL is unavailable.") from error
        except psycopg.IntegrityError as error:
            raise DataIntegrityError("PostgreSQL rejected inconsistent canonical data.") from error
        except psycopg.Error as error:
            raise StorePermanentError("PostgreSQL operation failed.") from error


def _text(value: object) -> str:
    if not isinstance(value, str):
        raise DataIntegrityError("PostgreSQL returned an invalid text value.")
    return value


def _optional_text(value: object) -> str | None:
    return None if value is None else _text(value)


def _integer(value: object) -> int:
    if not isinstance(value, int):
        raise DataIntegrityError("PostgreSQL returned an invalid integer value.")
    return value


def _datetime(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise DataIntegrityError("PostgreSQL returned an invalid timestamp.")
    return value
