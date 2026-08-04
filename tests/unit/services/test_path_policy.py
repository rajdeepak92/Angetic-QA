"""Document-root path policy tests for F-004."""

from __future__ import annotations

from pathlib import Path

import pytest

from multi_agentic_graph_rag.domain.errors import DomainValidationError
from multi_agentic_graph_rag.services.path_policy import validate_document_path


def test_validate_document_path_accepts_regular_files_under_root(tmp_path: Path) -> None:
    """A real document inside the configured root resolves to a typed source path."""
    document_root = tmp_path / "documents"
    document_root.mkdir()
    source_file = document_root / "sample.pdf"
    source_file.write_bytes(b"pdf-bytes")

    validated = validate_document_path("sample.pdf", document_root=document_root)

    assert validated.original_text == "sample.pdf"
    assert validated.document_root == document_root.resolve()
    assert validated.resolved_path == source_file.resolve()
    assert validated.extension == ".pdf"
    assert validated.size_bytes == source_file.stat().st_size


@pytest.mark.parametrize(
    ("raw_path", "filename", "message"),
    [
        ("../outside.pdf", "outside.pdf", "stay under the configured root"),
        ("sample.txt", "sample.txt", ".pdf or .docx"),
        ("empty.pdf", "empty.pdf", "outside the accepted range"),
        ("folder", "folder", "regular file"),
    ],
)
def test_validate_document_path_rejects_invalid_paths(
    tmp_path: Path,
    raw_path: str,
    filename: str,
    message: str,
) -> None:
    """Traversal, extension, size, and regular-file failures stay explicit."""
    document_root = tmp_path / "documents"
    document_root.mkdir()
    candidate = document_root / filename
    if filename == "folder":
        candidate.mkdir()
    elif filename == "empty.pdf":
        candidate.touch()
    else:
        candidate.write_text("content", encoding="utf-8")
    outside = tmp_path / "outside.pdf"
    outside.write_text("outside", encoding="utf-8")

    with pytest.raises(DomainValidationError, match=message):
        validate_document_path(raw_path, document_root=document_root)


def test_validate_document_path_rejects_symlinked_documents(tmp_path: Path) -> None:
    """Symlinked document paths are rejected before any file content is used."""
    document_root = tmp_path / "documents"
    document_root.mkdir()
    target = document_root / "target.pdf"
    target.write_text("content", encoding="utf-8")
    link = document_root / "linked.pdf"
    try:
        link.symlink_to(target)
    except (AttributeError, NotImplementedError, OSError) as error:
        pytest.skip(f"Symlink creation is unavailable in this environment: {error}")

    with pytest.raises(DomainValidationError, match="must not be a symlink"):
        validate_document_path("linked.pdf", document_root=document_root)


def test_validate_document_path_rejects_missing_root(tmp_path: Path) -> None:
    """An absent configured root fails before any candidate path is resolved."""
    with pytest.raises(DomainValidationError, match="root is not available"):
        validate_document_path("sample.pdf", document_root=tmp_path / "missing")
