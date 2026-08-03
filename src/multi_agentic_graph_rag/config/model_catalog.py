"""Approved provider and model catalog."""

from __future__ import annotations

from dataclasses import dataclass

from multi_agentic_graph_rag.domain.enums import Capability, Provider


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """Approved models for one provider capability."""

    capability: Capability
    provider: Provider
    models: tuple[str, ...]
    default_model: str | None
    uses_deployment_alias: bool = False


MODEL_CATALOG = (
    CatalogEntry(
        Capability.REASONING,
        Provider.OPENAI,
        ("gpt-5.6", "gpt-5.6-terra", "gpt-5.6-luna"),
        "gpt-5.6",
    ),
    CatalogEntry(
        Capability.REASONING,
        Provider.GOOGLE_GEMINI,
        ("gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.5-flash-lite"),
        "gemini-2.5-flash",
    ),
    CatalogEntry(Capability.REASONING, Provider.AZURE_OPENAI, (), None, True),
    CatalogEntry(
        Capability.EMBEDDING,
        Provider.OPENAI,
        ("text-embedding-3-small", "text-embedding-3-large"),
        "text-embedding-3-small",
    ),
    CatalogEntry(
        Capability.EMBEDDING,
        Provider.GOOGLE_GEMINI,
        ("gemini-embedding-2",),
        "gemini-embedding-2",
    ),
    CatalogEntry(Capability.EMBEDDING, Provider.AZURE_OPENAI, (), None, True),
    CatalogEntry(
        Capability.RERANKING,
        Provider.HUGGING_FACE,
        ("BAAI/bge-reranker-base", "cross-encoder/ms-marco-MiniLM-L6-v2"),
        "BAAI/bge-reranker-base",
    ),
)


def catalog_entry(capability: Capability, provider: Provider) -> CatalogEntry:
    """Return the catalog entry or reject an unsupported provider capability."""
    for entry in MODEL_CATALOG:
        if entry.capability is capability and entry.provider is provider:
            return entry
    raise ValueError(f"{provider.display_name} does not support {capability.value}.")


def providers_for(capability: Capability) -> tuple[Provider, ...]:
    """Return providers approved for a capability."""
    return tuple(entry.provider for entry in MODEL_CATALOG if entry.capability is capability)


def validate_model(capability: Capability, provider: Provider, model: str) -> None:
    """Reject a model outside its provider capability catalog."""
    entry = catalog_entry(capability, provider)
    if not entry.uses_deployment_alias and model not in entry.models:
        raise ValueError(
            f"{model!r} is not approved for {provider.display_name} {capability.value}."
        )
