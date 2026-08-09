"""Deterministic parsing and chunking tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from multi_agentic_graph_rag.domain.identifiers import deterministic_uuid7
from multi_agentic_graph_rag.domain.schemas.sources import DocumentBlock
from multi_agentic_graph_rag.services.chunking import build_chunks, build_source_ledger


def test_identical_bytes_have_identical_chunk_identity_order_and_checksums() -> None:
    project_id = deterministic_uuid7(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC), namespace="test", value="project"
    )
    run_id = deterministic_uuid7(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC), namespace="test", value="run"
    )
    content = b"same bytes"
    blocks = (DocumentBlock(block_index=0, text="alpha beta gamma"),)

    def make() -> object:
        ledger = build_source_ledger(
            project_id=project_id,
            run_id=run_id,
            source_path="sample.pdf",
            extension=".pdf",
            content=content,
            blocks=blocks,
        )
        return build_chunks(ledger=ledger, blocks=blocks, max_chars=10)

    first = make()
    second = make()
    assert first == second
    assert [chunk.ordinal for chunk in first.chunks] == [0, 1]
    assert all(len(chunk.text) <= 10 for chunk in first.chunks)


def test_chunking_rejects_a_token_larger_than_the_bound() -> None:
    project_id = deterministic_uuid7(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC), namespace="test", value="project"
    )
    run_id = deterministic_uuid7(
        timestamp=datetime(2024, 1, 1, tzinfo=UTC), namespace="test", value="run"
    )
    blocks = (DocumentBlock(block_index=0, text="toolong"),)
    ledger = build_source_ledger(
        project_id=project_id,
        run_id=run_id,
        source_path="sample.pdf",
        extension=".pdf",
        content=b"same bytes",
        blocks=blocks,
    )

    with pytest.raises(ValueError, match="A document token exceeds max_chars"):
        build_chunks(ledger=ledger, blocks=blocks, max_chars=3)
