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
