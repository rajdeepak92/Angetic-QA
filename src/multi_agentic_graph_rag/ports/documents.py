"""Ports for deterministic document extraction."""

from __future__ import annotations

from typing import Protocol

from multi_agentic_graph_rag.domain.schemas.sources import DocumentBlock


class DocumentReaderPort(Protocol):
    """Extract ordered blocks without changing their provenance."""

    def read(self, content: bytes) -> tuple[DocumentBlock, ...]:
        """Return blocks from document bytes."""
        ...
