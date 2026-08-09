"""Google Gemini embedding adapter."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from google import genai
from pydantic import SecretStr

from multi_agentic_graph_rag.domain.enums import Provider
from multi_agentic_graph_rag.domain.errors import ProviderPermanentError


class GeminiEmbeddingModel:
    """Embed text through Gemini while retaining credentials inside the adapter."""

    def __init__(self, *, model: str, api_key: SecretStr) -> None:
        self._model = model
        self._api_key = api_key

    @property
    def provider(self) -> Provider:
        """Return the configured provider."""
        return Provider.GOOGLE_GEMINI

    @property
    def model(self) -> str:
        """Return the configured model."""
        return self._model

    def embed(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        """Return Gemini vectors in input order."""
        if not texts or any(not text for text in texts):
            raise ValueError("Embedding input must contain non-empty text.")
        try:
            client: Any = genai.Client(api_key=self._api_key.get_secret_value())
            response: Any = client.models.embed_content(  # adapter SDK boundary
                model=self._model, contents=list(texts)
            )
            embeddings = response.embeddings or []
            return tuple(tuple(float(value) for value in item.values) for item in embeddings)
        except Exception as error:
            raise ProviderPermanentError("Gemini embedding failed.") from error
