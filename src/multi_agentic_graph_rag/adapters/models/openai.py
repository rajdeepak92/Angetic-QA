"""OpenAI embedding adapter."""

from __future__ import annotations

from collections.abc import Sequence

from openai import OpenAI
from pydantic import SecretStr

from multi_agentic_graph_rag.domain.enums import Provider
from multi_agentic_graph_rag.domain.errors import ProviderPermanentError


class OpenAIEmbeddingModel:
    """Embed text through OpenAI while retaining credentials inside the adapter."""

    def __init__(self, *, model: str, api_key: SecretStr) -> None:
        self._model = model
        self._api_key = api_key

    @property
    def provider(self) -> Provider:
        """Return the configured provider."""
        return Provider.OPENAI

    @property
    def model(self) -> str:
        """Return the configured model."""
        return self._model

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """Return OpenAI vectors in input order."""
        if not texts or any(not text for text in texts):
            raise ValueError("Embedding input must contain non-empty text.")
        try:
            response = OpenAI(api_key=self._api_key.get_secret_value()).embeddings.create(
                model=self._model, input=list(texts)
            )
            ordered = sorted(response.data, key=lambda item: item.index)
            return tuple(tuple(float(value) for value in item.embedding) for item in ordered)
        except Exception as error:
            raise ProviderPermanentError("OpenAI embedding failed.") from error
