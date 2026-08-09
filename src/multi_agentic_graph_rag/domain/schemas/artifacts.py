"""Strict canonical chunk artifact contracts."""

from __future__ import annotations

from typing import cast

from pydantic import BaseModel, Field

from multi_agentic_graph_rag.domain.identifiers import UUID7, Checksum, JsonValue, checksum_json
from multi_agentic_graph_rag.domain.schemas.sources import SOURCE_MODEL_CONFIG


class ChunkProvenance(BaseModel):
    """Source locations covered by one canonical chunk."""

    model_config = SOURCE_MODEL_CONFIG

    block_start: int = Field(ge=0)
    block_end: int = Field(ge=0)
    page_start: int | None = Field(default=None, ge=1)
    page_end: int | None = Field(default=None, ge=1)
    paragraph_start: int | None = Field(default=None, ge=0)
    paragraph_end: int | None = Field(default=None, ge=0)


class CanonicalChunk(BaseModel):
    """One immutable, bounded, project/run-scoped chunk."""

    model_config = SOURCE_MODEL_CONFIG

    schema_version: int = Field(default=1, ge=1)
    project_id: UUID7
    run_id: UUID7
    source_id: UUID7
    chunk_id: UUID7
    ordinal: int = Field(ge=0)
    text: str = Field(min_length=1)
    text_checksum: Checksum
    provenance: ChunkProvenance


class CanonicalChunks(BaseModel):
    """The immutable ordered chunk set for one source and run."""

    model_config = SOURCE_MODEL_CONFIG

    schema_version: int = Field(default=1, ge=1)
    project_id: UUID7
    run_id: UUID7
    source_id: UUID7
    chunks: tuple[CanonicalChunk, ...]
    checksum: Checksum


class EmbeddingFingerprint(BaseModel):
    """The provider/model/dimension identity of one embedding space."""

    model_config = SOURCE_MODEL_CONFIG

    provider: str = Field(min_length=1, max_length=50)
    model: str = Field(min_length=1, max_length=200)
    dimension: int = Field(ge=1)
    fingerprint: Checksum


class ManifestChunk(BaseModel):
    """Projection and embedding identity for one canonical chunk."""

    model_config = SOURCE_MODEL_CONFIG

    chunk_id: UUID7
    ordinal: int = Field(ge=0)
    text_checksum: Checksum
    embedding_checksum: Checksum


class ChunkManifest(BaseModel):
    """Immutable project/run artifact describing verified chunk projections."""

    model_config = SOURCE_MODEL_CONFIG

    schema_version: int = Field(default=1, ge=1)
    project_id: UUID7
    run_id: UUID7
    source_id: UUID7
    embedding: EmbeddingFingerprint
    chunks: tuple[ManifestChunk, ...]
    checksum: Checksum

    @classmethod
    def create(
        cls,
        *,
        project_id: UUID7,
        run_id: UUID7,
        source_id: UUID7,
        embedding: EmbeddingFingerprint,
        chunks: tuple[ManifestChunk, ...],
    ) -> ChunkManifest:
        """Create a manifest with a deterministic checksum over its content."""
        content = {
            "schema_version": 1,
            "project_id": str(project_id),
            "run_id": str(run_id),
            "source_id": str(source_id),
            "embedding": embedding.model_dump(mode="json"),
            "chunks": [chunk.model_dump(mode="json") for chunk in chunks],
        }
        return cls(
            schema_version=1,
            project_id=project_id,
            run_id=run_id,
            source_id=source_id,
            embedding=embedding,
            chunks=chunks,
            checksum=checksum_json(cast(JsonValue, content)),
        )
