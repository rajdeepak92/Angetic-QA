"""Docker-backed PostgreSQL and Neo4j persistence integration tests."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import psycopg
import pytest
from neo4j import GraphDatabase

from multi_agentic_graph_rag.adapters.persistence.neo4j import Neo4jProjectionRepository
from multi_agentic_graph_rag.adapters.persistence.postgres import PostgresRunRepository
from multi_agentic_graph_rag.config.loader import (
    load_persistence_credentials,
    load_settings,
)
from multi_agentic_graph_rag.domain.enums import RunStatus, TargetStage
from multi_agentic_graph_rag.domain.errors import NotFoundError
from multi_agentic_graph_rag.domain.identifiers import checksum_json, new_uuid7
from multi_agentic_graph_rag.domain.schemas.runs import ProjectionScope, ProjectRecord, RunRecord

pytestmark = pytest.mark.integration


def _live_settings():
    if not os.environ.get("MAGR_POSTGRES_PASSWORD") or not os.environ.get("MAGR_NEO4J_PASSWORD"):
        pytest.skip("Docker persistence credentials are not configured.")
    return load_settings(Path("config.json")), load_persistence_credentials()


def test_postgres_schema_is_idempotent_and_runs_are_project_isolated() -> None:
    """Canonical schema/readback works twice and requires project plus run ID."""
    settings, credentials = _live_settings()
    repository = PostgresRunRepository(settings.persistence, credentials)
    repository.initialize_schema()
    repository.initialize_schema()
    now = datetime.now(UTC)
    project_id = new_uuid7()
    other_project_id = new_uuid7()
    run_id = new_uuid7()
    project = ProjectRecord(project_id=project_id, name="Integration project", created_at=now)
    run = RunRecord(
        project_id=project_id,
        run_id=run_id,
        target_stage=TargetStage.REQUIREMENTS,
        status=RunStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    repository.save_project(project)
    repository.save_run(run)

    try:
        assert repository.get_run(project_id=project_id, run_id=run_id) == run
        with pytest.raises(NotFoundError):
            repository.get_run(project_id=other_project_id, run_id=run_id)
        assert repository.check_health().is_ready
    finally:
        password = credentials.postgres_password
        assert password is not None
        with (
            psycopg.connect(
                host=settings.persistence.postgres_host,
                port=settings.persistence.postgres_port,
                dbname=settings.persistence.postgres_database,
                user=settings.persistence.postgres_user,
                password=password.get_secret_value(),
            ) as connection,
            connection.cursor() as cursor,
        ):
            cursor.execute(
                "DELETE FROM agentic_qa.runs WHERE project_id = %s AND run_id = %s",
                (project_id, run_id),
            )
            cursor.execute("DELETE FROM agentic_qa.projects WHERE project_id = %s", (project_id,))


def test_neo4j_scope_is_idempotent_and_project_isolated() -> None:
    """Rebuildable Neo4j metadata supports scoped upsert and readback."""
    settings, credentials = _live_settings()
    repository = Neo4jProjectionRepository(settings.persistence, credentials)
    project_id = new_uuid7()
    missing_project_id = new_uuid7()
    scope = ProjectionScope(
        project_id=project_id,
        source_checksum=checksum_json({"project_id": str(project_id)}),
    )

    try:
        assert repository.ensure_scope(scope) == scope
        assert repository.ensure_scope(scope) == scope
        assert repository.get_scope(project_id=project_id) == scope
        with pytest.raises(NotFoundError):
            repository.get_scope(project_id=missing_project_id)
        assert repository.check_health().is_ready
    finally:
        password = credentials.neo4j_password
        assert password is not None
        with GraphDatabase.driver(
            settings.persistence.neo4j_uri,
            auth=(settings.persistence.neo4j_user, password.get_secret_value()),
        ) as driver:
            driver.execute_query(
                "MATCH (scope:ProjectionScope {project_id: $project_id}) DELETE scope",
                project_id=str(project_id),
                database_="neo4j",
            )
