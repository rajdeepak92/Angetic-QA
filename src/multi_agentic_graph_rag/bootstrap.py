"""Application composition root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from multi_agentic_graph_rag.adapters.models.factory import HttpModelConnectionAdapter
from multi_agentic_graph_rag.adapters.persistence.chroma import ChromaProjectionRepository
from multi_agentic_graph_rag.adapters.persistence.neo4j import Neo4jProjectionRepository
from multi_agentic_graph_rag.adapters.persistence.postgres import PostgresRunRepository
from multi_agentic_graph_rag.config.loader import load_persistence_credentials, load_settings
from multi_agentic_graph_rag.config.settings import AppSettings
from multi_agentic_graph_rag.ports.models import ModelConnectionPort
from multi_agentic_graph_rag.ports.repositories import (
    PersistenceHealthPort,
    ProjectionScopePort,
    RunRepositoryPort,
)


@dataclass(frozen=True, slots=True)
class AppContext:
    """Dependencies shared by the Streamlit pages."""

    default_settings: AppSettings
    connection_adapter: ModelConnectionPort
    run_repository: RunRepositoryPort
    projection_repositories: tuple[ProjectionScopePort, ...]

    @property
    def persistence_checks(self) -> tuple[PersistenceHealthPort, ...]:
        """Return every configured store behind its health port."""
        return (self.run_repository, *self.projection_repositories)


def build_app_context(config_path: Path = Path("config.json")) -> AppContext:
    """Load validated settings and wire stateless provider adapters."""
    settings = load_settings(config_path)
    credentials = load_persistence_credentials()
    return AppContext(
        default_settings=settings,
        connection_adapter=HttpModelConnectionAdapter(),
        run_repository=PostgresRunRepository(settings.persistence, credentials),
        projection_repositories=(
            Neo4jProjectionRepository(settings.persistence, credentials),
            ChromaProjectionRepository(settings.persistence),
        ),
    )
