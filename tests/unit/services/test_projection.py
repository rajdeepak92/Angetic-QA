"""F-006 projection service tests without provider or database services."""

from __future__ import annotations

from pathlib import Path

from multi_agentic_graph_rag.domain.enums import Provider
from multi_agentic_graph_rag.domain.identifiers import checksum_bytes, new_uuid7
from multi_agentic_graph_rag.domain.schemas.artifacts import (
    CanonicalChunk,
    CanonicalChunks,
    ChunkProvenance,
)
from multi_agentic_graph_rag.services.projection import project_chunks


class FakeEmbeddingModel:
    """Deterministic embedding provider fake."""

    provider = Provider.OPENAI
    model = "fake-embedding"

    def embed(self, texts: list[str]) -> tuple[tuple[float, ...], ...]:
        return tuple((float(len(text)), 1.0) for text in texts)


class FakeProjection:
    """In-memory projection fake with readback."""

    def __init__(self) -> None:
        self.ids: tuple = ()

    def upsert_chunks(self, *, chunks, embeddings, fingerprint) -> None:
        self.ids = tuple(chunk.chunk_id for chunk in chunks.chunks)

    def read_chunk_ids(self, *, project_id, chunk_ids):
        return tuple(chunk_id for chunk_id in chunk_ids if chunk_id in self.ids)


def test_projection_writes_manifest_after_deterministic_readback(tmp_path: Path) -> None:
    project_id, run_id, source_id = new_uuid7(), new_uuid7(), new_uuid7()
    chunk_id = new_uuid7()
    chunk = CanonicalChunk(
        project_id=project_id,
        run_id=run_id,
        source_id=source_id,
        chunk_id=chunk_id,
        ordinal=0,
        text="bounded text",
        text_checksum=checksum_bytes(b"bounded text"),
        provenance=ChunkProvenance(block_start=0, block_end=0),
    )
    chunks = CanonicalChunks(
        project_id=project_id,
        run_id=run_id,
        source_id=source_id,
        chunks=(chunk,),
        checksum=checksum_bytes(b"chunks"),
    )

    manifest = project_chunks(
        chunks,
        embedding_model=FakeEmbeddingModel(),
        neo4j=FakeProjection(),
        chroma=FakeProjection(),
        generated_root=tmp_path,
    )

    path = tmp_path / str(project_id) / str(run_id) / "requirements" / "chunk_manifest.json"
    assert manifest.chunks[0].chunk_id == chunk_id
    assert manifest.embedding.dimension == 2
    assert path.exists()
    assert (
        project_chunks(
            chunks,
            embedding_model=FakeEmbeddingModel(),
            neo4j=FakeProjection(),
            chroma=FakeProjection(),
            generated_root=tmp_path,
        )
        == manifest
    )
