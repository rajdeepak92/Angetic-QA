"""Application composition root."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from multi_agentic_graph_rag.adapters.documents.docx_reader import DocxReader
from multi_agentic_graph_rag.adapters.documents.pdf_reader import PdfReader
from multi_agentic_graph_rag.adapters.models.factory import HttpModelConnectionAdapter
from multi_agentic_graph_rag.adapters.models.gemini import GeminiEmbeddingModel
from multi_agentic_graph_rag.adapters.models.openai import OpenAIEmbeddingModel
from multi_agentic_graph_rag.adapters.persistence.chroma import ChromaProjectionRepository
from multi_agentic_graph_rag.adapters.persistence.neo4j import Neo4jProjectionRepository
from multi_agentic_graph_rag.adapters.persistence.postgres import PostgresRunRepository
from multi_agentic_graph_rag.config.loader import load_persistence_credentials, load_settings
from multi_agentic_graph_rag.config.settings import AppSettings, CredentialBundle
from multi_agentic_graph_rag.domain.enums import Provider
from multi_agentic_graph_rag.domain.errors import ProviderPermanentError
from multi_agentic_graph_rag.ports.models import EmbeddingModelPort, ModelConnectionPort
from multi_agentic_graph_rag.ports.repositories import (
    PersistenceHealthPort,
    ProjectionScopePort,
    RunRepositoryPort,
)
from multi_agentic_graph_rag.services.run_coordinator import RunCoordinator


@dataclass(frozen=True, slots=True)
class AppContext:
    """Dependencies shared by the Streamlit pages."""

    default_settings: AppSettings
    connection_adapter: ModelConnectionPort
    run_repository: RunRepositoryPort
    projection_repositories: tuple[ProjectionScopePort, ...]
    run_coordinator: RunCoordinator
    embedding_model_factory: Callable[[AppSettings, CredentialBundle], EmbeddingModelPort]

    @property
    def persistence_checks(self) -> tuple[PersistenceHealthPort, ...]:
        """Return every configured store behind its health port."""
        return (self.run_repository, *self.projection_repositories)


def build_app_context(config_path: Path = Path("config.json")) -> AppContext:
    """Load validated settings and wire stateless provider adapters."""
    settings = load_settings(config_path)
    credentials = load_persistence_credentials()
    run_repository = PostgresRunRepository(settings.persistence, credentials)
    neo4j_repository = Neo4jProjectionRepository(settings.persistence, credentials)
    chroma_repository = ChromaProjectionRepository(settings.persistence)
    embedding_model_factory = _embedding_model_factory
    return AppContext(
        default_settings=settings,
        connection_adapter=HttpModelConnectionAdapter(),
        run_repository=run_repository,
        projection_repositories=(
            neo4j_repository,
            chroma_repository,
        ),
        run_coordinator=RunCoordinator(
            repository=run_repository,
            readers={".pdf": PdfReader(), ".docx": DocxReader()},
            embedding_model_factory=embedding_model_factory,
            neo4j=neo4j_repository,
            chroma=chroma_repository,
        ),
        embedding_model_factory=embedding_model_factory,
    )


def _embedding_model_factory(
    settings: AppSettings, credentials: CredentialBundle
) -> EmbeddingModelPort:
    """Construct one embedding adapter from session settings and credentials."""
    selection = settings.embedding
    secret = credentials.secret_for(selection.provider)
    if secret is None:
        raise ProviderPermanentError("Embedding provider credential is required.")
    if selection.provider is Provider.OPENAI:
        return OpenAIEmbeddingModel(model=selection.model, api_key=secret)
    if selection.provider is Provider.GOOGLE_GEMINI:
        return GeminiEmbeddingModel(model=selection.model, api_key=secret)
    raise ProviderPermanentError("The selected embedding provider is not supported by F-006.")
