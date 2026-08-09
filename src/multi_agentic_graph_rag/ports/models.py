"""Typed model-provider connection port."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from pydantic import SecretStr

from multi_agentic_graph_rag.domain.enums import Capability, Provider


@dataclass(frozen=True, slots=True)
class ConnectionCheckRequest:
    """Validated values required for one bounded provider probe."""

    provider: Provider
    capability: Capability
    target: str
    secret: SecretStr | None
    endpoint: str | None
    revision: str | None
    offline_mode: bool
    timeout_seconds: int


@dataclass(frozen=True, slots=True)
class ConnectionCheckResult:
    """Sanitized provider probe result safe for UI and session state."""

    provider: Provider
    capability: Capability
    target: str
    is_success: bool
    latency_ms: int
    detail: str


class ModelConnectionPort(Protocol):
    """Probe one selected provider capability without exposing vendor responses."""

    def check(self, request: ConnectionCheckRequest) -> ConnectionCheckResult:
        """Return a bounded sanitized connection result."""
        ...


class EmbeddingModelPort(Protocol):
    """Embed bounded text batches without exposing provider credentials."""

    @property
    def provider(self) -> Provider:
        """Return the configured provider identity."""
        ...

    @property
    def model(self) -> str:
        """Return the configured model identity."""
        ...

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """Return vectors in the exact input order."""
        ...
