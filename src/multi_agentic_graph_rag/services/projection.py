"""Stage 1.1b embedding, projection, readback, and manifest service."""

from __future__ import annotations

from pathlib import Path

from multi_agentic_graph_rag.domain.identifiers import (
    canonical_json_bytes,
    checksum_bytes,
    checksum_json,
)
from multi_agentic_graph_rag.domain.schemas.artifacts import (
    CanonicalChunks,
    ChunkManifest,
    EmbeddingFingerprint,
    ManifestChunk,
)
from multi_agentic_graph_rag.ports.models import EmbeddingModelPort
from multi_agentic_graph_rag.ports.repositories import ChunkProjectionPort


def project_chunks(
    chunks: CanonicalChunks,
    *,
    embedding_model: EmbeddingModelPort,
    neo4j: ChunkProjectionPort,
    chroma: ChunkProjectionPort,
    generated_root: Path,
) -> ChunkManifest:
    """Embed canonical chunks, project them, verify readback, and publish a manifest."""
    vectors = embedding_model.embed(tuple(chunk.text for chunk in chunks.chunks))
    if len(vectors) != len(chunks.chunks):
        raise ValueError("Embedding count does not match canonical chunk count.")
    dimension = len(vectors[0]) if vectors else 0
    if dimension == 0 or any(len(vector) != dimension for vector in vectors):
        raise ValueError("Embedding vectors must have one consistent positive dimension.")
    fingerprint = EmbeddingFingerprint(
        provider=embedding_model.provider.value,
        model=embedding_model.model,
        dimension=dimension,
        fingerprint=checksum_json(
            {
                "provider": embedding_model.provider.value,
                "model": embedding_model.model,
                "dimension": dimension,
            }
        ),
    )
    neo4j.upsert_chunks(chunks=chunks, embeddings=vectors, fingerprint=fingerprint)
    chroma.upsert_chunks(chunks=chunks, embeddings=vectors, fingerprint=fingerprint)
    expected_ids = tuple(chunk.chunk_id for chunk in chunks.chunks)
    if set(neo4j.read_chunk_ids(project_id=chunks.project_id, chunk_ids=expected_ids)) != set(
        expected_ids
    ):
        raise ValueError("Neo4j chunk readback did not match the canonical chunks.")
    if set(chroma.read_chunk_ids(project_id=chunks.project_id, chunk_ids=expected_ids)) != set(
        expected_ids
    ):
        raise ValueError("Chroma chunk readback did not match the canonical chunks.")
    manifest = ChunkManifest.create(
        project_id=chunks.project_id,
        run_id=chunks.run_id,
        source_id=chunks.source_id,
        embedding=fingerprint,
        chunks=tuple(
            ManifestChunk(
                chunk_id=chunk.chunk_id,
                ordinal=chunk.ordinal,
                text_checksum=chunk.text_checksum,
                embedding_checksum=checksum_bytes(canonical_json_bytes(list(vector))),
            )
            for chunk, vector in zip(chunks.chunks, vectors, strict=True)
        ),
    )
    _write_immutable_manifest(generated_root, manifest)
    return manifest


def _write_immutable_manifest(generated_root: Path, manifest: ChunkManifest) -> Path:
    """Publish one project/run-scoped manifest without overwriting a different artifact."""
    path = (
        generated_root
        / str(manifest.project_id)
        / str(manifest.run_id)
        / "requirements"
        / "chunk_manifest.json"
    )
    payload = canonical_json_bytes(manifest.model_dump(mode="json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError("A different chunk manifest already exists for this run.")
        return path
    temporary = path.with_suffix(".json.tmp")
    temporary.write_bytes(payload)
    try:
        temporary.replace(path)
    except FileExistsError:
        temporary.unlink(missing_ok=True)
        if path.read_bytes() != payload:
            raise
    return path
