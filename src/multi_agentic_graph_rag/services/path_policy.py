"""Document-root path validation for workflow requests."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

from multi_agentic_graph_rag.domain.errors import DomainValidationError
from multi_agentic_graph_rag.domain.schemas.sources import SourcePath

MAX_DOCUMENT_SIZE_BYTES = 100 * 1024 * 1024
SUPPORTED_DOCUMENT_EXTENSIONS = {".pdf", ".docx"}


def validate_document_path(
    raw_path: str,
    *,
    document_root: Path,
    max_size_bytes: int = MAX_DOCUMENT_SIZE_BYTES,
) -> SourcePath:
    """Resolve and validate one source document under the configured root."""
    if not raw_path or raw_path != raw_path.strip():
        raise DomainValidationError("Document path must be explicit and unambiguous.")
    try:
        root = document_root.resolve(strict=True)
    except OSError as error:
        raise DomainValidationError("Document root is not available.") from error
    if not root.is_dir():
        raise DomainValidationError("Document root is not available.")

    candidate = Path(raw_path)
    candidate = candidate if candidate.is_absolute() else root / candidate
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as error:
        raise DomainValidationError("Document path was not found.") from error

    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise DomainValidationError("Document path must stay under the configured root.") from error
    if candidate.is_symlink():
        raise DomainValidationError("Document path must not be a symlink.")
    if not resolved.is_file():
        raise DomainValidationError("Document path must reference a regular file.")
    extension = resolved.suffix.casefold()
    if extension not in SUPPORTED_DOCUMENT_EXTENSIONS:
        raise DomainValidationError("Document must be a .pdf or .docx file.")
    extension = cast(Literal[".pdf", ".docx"], extension)
    size_bytes = resolved.stat().st_size
    if size_bytes <= 0 or size_bytes > max_size_bytes:
        raise DomainValidationError("Document size is outside the accepted range.")
    return SourcePath(
        original_text=raw_path,
        document_root=root,
        resolved_path=resolved,
        extension=extension,
        size_bytes=size_bytes,
    )
