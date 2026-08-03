"""Application composition root."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from multi_agentic_graph_rag.adapters.models.factory import HttpModelConnectionAdapter
from multi_agentic_graph_rag.config.loader import load_settings
from multi_agentic_graph_rag.config.settings import AppSettings
from multi_agentic_graph_rag.ports.models import ModelConnectionPort


@dataclass(frozen=True, slots=True)
class AppContext:
    """Dependencies shared by the Streamlit pages."""

    default_settings: AppSettings
    connection_adapter: ModelConnectionPort


def build_app_context(config_path: Path = Path("config.json")) -> AppContext:
    """Load validated settings and wire stateless provider adapters."""
    return AppContext(
        default_settings=load_settings(config_path),
        connection_adapter=HttpModelConnectionAdapter(),
    )
