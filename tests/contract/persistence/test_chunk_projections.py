"""Projection adapter contract tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from multi_agentic_graph_rag.adapters.persistence.chroma import ChromaProjectionRepository
from multi_agentic_graph_rag.config.loader import load_settings
from multi_agentic_graph_rag.config.settings import PersistenceSettings
from multi_agentic_graph_rag.domain.enums import Provider
from multi_agentic_graph_rag.domain.errors import DataIntegrityError
from multi_agentic_graph_rag.domain.identifiers import checksum_bytes, checksum_json, new_uuid7
from multi_agentic_graph_rag.domain.schemas.artifacts import (
    CanonicalChunk,
    CanonicalChunks,
    ChunkProvenance,
    EmbeddingFingerprint,
)


def test_chroma_chunk_upsert_readback_and_fingerprint_boundary(tmp_path: Path) -> None:
    base = load_settings(Path("config.json"), environment={}).persistence
    values = {name: getattr(base, name) for name in type(base).model_fields}
    values["chroma_path"] = tmp_path / "chroma"
    repository = ChromaProjectionRepository(PersistenceSettings(**values))
    project_id, run_id, source_id, chunk_id = new_uuid7(), new_uuid7(), new_uuid7(), new_uuid7()
    chunk = CanonicalChunk(
        project_id=project_id,
        run_id=run_id,
        source_id=source_id,
        chunk_id=chunk_id,
        ordinal=0,
        text="text",
        text_checksum=checksum_bytes(b"text"),
        provenance=ChunkProvenance(block_start=0, block_end=0),
    )
    chunks = CanonicalChunks(
        project_id=project_id,
        run_id=run_id,
        source_id=source_id,
        chunks=(chunk,),
        checksum=checksum_bytes(b"chunks"),
    )
    fingerprint = EmbeddingFingerprint(
        provider=Provider.OPENAI.value,
        model="fake",
        dimension=2,
        fingerprint=checksum_json({"model": "fake", "dimension": 2}),
    )

    repository.upsert_chunks(chunks=chunks, embeddings=((1.0, 2.0),), fingerprint=fingerprint)

    assert repository.read_chunk_ids(project_id=project_id, chunk_ids=(chunk_id,)) == (chunk_id,)
    incompatible = fingerprint.model_copy(update={"dimension": 3})
    with pytest.raises(DataIntegrityError):
        repository.upsert_chunks(
            chunks=chunks, embeddings=((1.0, 2.0, 3.0),), fingerprint=incompatible
        )
