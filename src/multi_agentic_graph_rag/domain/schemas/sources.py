"""Strict source-document and provenance contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from multi_agentic_graph_rag.domain.identifiers import UUID7, Checksum

SOURCE_MODEL_CONFIG = ConfigDict(
    strict=True,
    extra="forbid",
    frozen=True,
    validate_default=True,
)


class SourcePath(BaseModel):
    """A canonical document path validated against the configured document root."""

    model_config = SOURCE_MODEL_CONFIG

    original_text: str = Field(min_length=1, max_length=1000)
    document_root: Path
    resolved_path: Path
    extension: Literal[".pdf", ".docx"]
    size_bytes: int = Field(ge=1)


class DocumentBlock(BaseModel):
    """One extracted block with format-specific provenance."""

    model_config = SOURCE_MODEL_CONFIG

    block_index: int = Field(ge=0)
    text: str = Field(min_length=1)
    page_number: int | None = Field(default=None, ge=1)
    paragraph_index: int | None = Field(default=None, ge=0)


class SourceLedger(BaseModel):
    """Canonical identity and extraction summary for one source."""

    model_config = SOURCE_MODEL_CONFIG

    schema_version: int = Field(default=1, ge=1)
    project_id: UUID7
    run_id: UUID7
    source_id: UUID7
    source_path: str = Field(min_length=1, max_length=1000)
    extension: Literal[".pdf", ".docx"]
    byte_checksum: Checksum
    normalized_checksum: Checksum
    block_count: int = Field(ge=0)
