"""Bounded, deterministic native text chunking."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from multi_agentic_graph_rag.domain.identifiers import (
    UUID7,
    canonical_json_bytes,
    checksum_bytes,
    checksum_json,
    deterministic_uuid7,
)
from multi_agentic_graph_rag.domain.schemas.artifacts import (
    CanonicalChunk,
    CanonicalChunks,
    ChunkProvenance,
)
from multi_agentic_graph_rag.domain.schemas.sources import DocumentBlock, SourceLedger

_IDENTITY_TIME = datetime(1970, 1, 1, tzinfo=UTC)


def build_source_ledger(
    *,
    project_id: UUID7,
    run_id: UUID7,
    source_path: str,
    extension: Literal[".pdf", ".docx"],
    content: bytes,
    blocks: tuple[DocumentBlock, ...],
) -> SourceLedger:
    """Build a content-derived source ledger without model-generated fields."""
    byte_checksum = checksum_bytes(content)
    normalized_checksum = checksum_json([block.text for block in blocks])
    source_id = deterministic_uuid7(
        timestamp=_IDENTITY_TIME,
        namespace="source",
        value={"project_id": str(project_id), "run_id": str(run_id), "checksum": byte_checksum},
    )
    return SourceLedger(
        project_id=project_id,
        run_id=run_id,
        source_id=source_id,
        source_path=source_path,
        extension=extension,
        byte_checksum=byte_checksum,
        normalized_checksum=normalized_checksum,
        block_count=len(blocks),
    )


def build_chunks(
    *, ledger: SourceLedger, blocks: tuple[DocumentBlock, ...], max_chars: int = 1200
) -> CanonicalChunks:
    """Pack whole words into bounded chunks while retaining block provenance."""
    if max_chars < 1:
        raise ValueError("max_chars must be positive.")
    chunks: list[CanonicalChunk] = []
    current: list[str] = []
    start = 0

    def flush(end: int) -> None:
        if not current:
            return
        text = " ".join(current)
        covered = blocks[start : end + 1]
        provenance = ChunkProvenance(
            block_start=start,
            block_end=end,
            page_start=next((b.page_number for b in covered if b.page_number), None),
            page_end=next((b.page_number for b in reversed(covered) if b.page_number), None),
            paragraph_start=next(
                (b.paragraph_index for b in covered if b.paragraph_index is not None), None
            ),
            paragraph_end=next(
                (b.paragraph_index for b in reversed(covered) if b.paragraph_index is not None),
                None,
            ),
        )
        ordinal = len(chunks)
        chunk_id = deterministic_uuid7(
            timestamp=_IDENTITY_TIME,
            namespace="chunk",
            value={"source_id": str(ledger.source_id), "ordinal": ordinal, "text": text},
        )
        chunks.append(
            CanonicalChunk(
                project_id=ledger.project_id,
                run_id=ledger.run_id,
                source_id=ledger.source_id,
                chunk_id=chunk_id,
                ordinal=ordinal,
                text=text,
                text_checksum=checksum_bytes(text.encode("utf-8")),
                provenance=provenance,
            )
        )
        current.clear()

    for index, block in enumerate(blocks):
        for word in block.text.split():
            if len(word) > max_chars:
                raise ValueError("A document token exceeds max_chars.")
            if current and len(" ".join((*current, word))) > max_chars:
                flush(index)
                start = index
            current.append(word)
    if blocks:
        flush(len(blocks) - 1)
    checksum = checksum_bytes(
        canonical_json_bytes([chunk.model_dump(mode="json") for chunk in chunks])
    )
    return CanonicalChunks(
        project_id=ledger.project_id,
        run_id=ledger.run_id,
        source_id=ledger.source_id,
        chunks=tuple(chunks),
        checksum=checksum,
    )
