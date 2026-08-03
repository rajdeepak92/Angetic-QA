"""Connection adapter contract tests without live provider calls."""

from __future__ import annotations

from types import TracebackType
from unittest.mock import patch
from urllib.error import HTTPError

import pytest
from pydantic import SecretStr

from multi_agentic_graph_rag.adapters.models.factory import HttpModelConnectionAdapter
from multi_agentic_graph_rag.domain.enums import Capability, Provider
from multi_agentic_graph_rag.ports.models import ConnectionCheckRequest


class _Response:
    def __enter__(self) -> _Response:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def getcode(self) -> int:
        return 200


@pytest.mark.parametrize(
    ("provider", "capability", "target", "endpoint", "revision", "secret"),
    [
        (Provider.OPENAI, Capability.REASONING, "gpt-5.6", None, None, "openai-secret"),
        (
            Provider.GOOGLE_GEMINI,
            Capability.EMBEDDING,
            "gemini-embedding-2",
            None,
            None,
            "google-secret",
        ),
        (
            Provider.AZURE_OPENAI,
            Capability.EMBEDDING,
            "embedding-deployment",
            "https://example.openai.azure.com",
            None,
            "azure-secret",
        ),
        (
            Provider.HUGGING_FACE,
            Capability.RERANKING,
            "BAAI/bge-reranker-base",
            None,
            "main",
            None,
        ),
    ],
)
def test_connection_adapter_success_is_sanitized(
    provider: Provider,
    capability: Capability,
    target: str,
    endpoint: str | None,
    revision: str | None,
    secret: str | None,
) -> None:
    """Every approved provider returns the same safe result contract."""
    request = ConnectionCheckRequest(
        provider=provider,
        capability=capability,
        target=target,
        secret=SecretStr(secret) if secret is not None else None,
        endpoint=endpoint,
        revision=revision,
        offline_mode=False,
        timeout_seconds=10,
    )
    with patch("multi_agentic_graph_rag.adapters.models.factory.urlopen", return_value=_Response()):
        result = HttpModelConnectionAdapter().check(request)

    assert result.is_success
    assert result.detail == "Connection succeeded."
    if secret is not None:
        assert secret not in repr(result)


def test_connection_adapter_failure_never_exposes_provider_payload_or_secret() -> None:
    """Authentication failures expose only the HTTP status category."""
    secret = "not-for-output"
    request = ConnectionCheckRequest(
        provider=Provider.GOOGLE_GEMINI,
        capability=Capability.REASONING,
        target="gemini-2.5-flash",
        secret=SecretStr(secret),
        endpoint=None,
        revision=None,
        offline_mode=False,
        timeout_seconds=10,
    )
    error = HTTPError(
        f"https://provider.invalid?key={secret}",
        401,
        "raw provider error",
        None,
        None,
    )
    with patch("multi_agentic_graph_rag.adapters.models.factory.urlopen", side_effect=error):
        result = HttpModelConnectionAdapter().check(request)

    assert not result.is_success
    assert result.detail == "Provider returned HTTP 401."
    assert secret not in repr(result)
    assert "raw provider error" not in repr(result)


def test_connection_adapter_does_not_call_network_without_required_credential() -> None:
    """Cloud probes fail before I/O when a credential is missing."""
    request = ConnectionCheckRequest(
        provider=Provider.OPENAI,
        capability=Capability.REASONING,
        target="gpt-5.6",
        secret=None,
        endpoint=None,
        revision=None,
        offline_mode=False,
        timeout_seconds=10,
    )
    with patch("multi_agentic_graph_rag.adapters.models.factory.urlopen") as opener:
        result = HttpModelConnectionAdapter().check(request)

    assert not result.is_success
    assert result.detail == "Credential is required."
    opener.assert_not_called()
