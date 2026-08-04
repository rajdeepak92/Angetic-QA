"""Stable provider and capability vocabulary."""

from __future__ import annotations

from enum import StrEnum


class Capability(StrEnum):
    """Model capability selected by the application."""

    REASONING = "reasoning"
    EMBEDDING = "embedding"
    RERANKING = "reranking"


class Provider(StrEnum):
    """Approved model provider."""

    OPENAI = "openai"
    GOOGLE_GEMINI = "google_gemini"
    AZURE_OPENAI = "azure_openai"
    HUGGING_FACE = "hugging_face"

    @property
    def display_name(self) -> str:
        """Return the provider label shown in the UI."""
        return {
            Provider.OPENAI: "OpenAI",
            Provider.GOOGLE_GEMINI: "Google Gemini",
            Provider.AZURE_OPENAI: "Azure OpenAI",
            Provider.HUGGING_FACE: "Hugging Face",
        }[self]


class RerankerDevice(StrEnum):
    """Allowed local reranker execution device."""

    AUTO = "auto"
    CPU = "cpu"
    CUDA = "cuda"


class TargetStage(StrEnum):
    """Requested final product stage for a run."""

    REQUIREMENTS = "requirements"
    USER_STORIES = "user_stories"
    TEST_SCENARIOS = "test_scenarios"


class RunStatus(StrEnum):
    """Persisted lifecycle state of one run."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class ErrorCategory(StrEnum):
    """Stable failure categories used across domain and adapter boundaries."""

    VALIDATION = "validation"
    CONFLICT = "conflict"
    NOT_FOUND = "not_found"
    TRANSIENT_PROVIDER = "transient_provider"
    TRANSIENT_STORE = "transient_store"
    PERMANENT_PROVIDER = "permanent_provider"
    PERMANENT_STORE = "permanent_store"
    INTEGRITY = "integrity"
    CANCELLATION = "cancellation"
