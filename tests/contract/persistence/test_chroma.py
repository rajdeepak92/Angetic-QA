"""Embedded Chroma projection-scope contract tests."""

from __future__ import annotations

from pathlib import Path

from multi_agentic_graph_rag.adapters.persistence.chroma import ChromaProjectionRepository
from multi_agentic_graph_rag.config.loader import load_settings
from multi_agentic_graph_rag.config.settings import PersistenceSettings
from multi_agentic_graph_rag.domain.identifiers import checksum_json, new_uuid7
from multi_agentic_graph_rag.domain.schemas.runs import ProjectionScope


def test_chroma_scope_is_project_isolated_and_persistent(tmp_path: Path) -> None:
    """A project scope survives adapter recreation without cross-project lookup."""
    base = load_settings(Path("config.json"), environment={}).persistence
    values = {name: getattr(base, name) for name in type(base).model_fields}
    values["chroma_path"] = tmp_path / "chroma"
    settings = PersistenceSettings(**values)
    project_id = new_uuid7()
    scope = ProjectionScope(
        project_id=project_id,
        source_checksum=checksum_json({"project_id": str(project_id)}),
    )

    first = ChromaProjectionRepository(settings)
    assert first.ensure_scope(scope) == scope
    assert first.check_health().is_ready
    assert ChromaProjectionRepository(settings).get_scope(project_id=project_id) == scope
