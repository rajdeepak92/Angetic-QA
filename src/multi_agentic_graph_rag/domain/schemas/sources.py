"""Strict source-document references accepted by workflow requests."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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
