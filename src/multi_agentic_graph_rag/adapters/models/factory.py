"""Build bounded standard-library connection probes for approved providers."""

from __future__ import annotations

import json
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from multi_agentic_graph_rag.domain.enums import Capability, Provider
from multi_agentic_graph_rag.ports.models import (
    ConnectionCheckRequest,
    ConnectionCheckResult,
)

_AZURE_API_VERSION = "2024-10-21"
_USER_AGENT = "GraphRAG-Agents/0.1"


class HttpModelConnectionAdapter:
    """Probe one configured provider without retaining clients or credentials."""

    def check(self, request: ConnectionCheckRequest) -> ConnectionCheckResult:
        """Make one bounded request and discard all provider response content."""
        started = monotonic()
        if request.offline_mode:
            return _result(request, started, False, "Offline mode prevents a remote check.")
        if request.provider is not Provider.HUGGING_FACE and request.secret is None:
            return _result(request, started, False, "Credential is required.")

        try:
            provider_request = _provider_request(request)
            with urlopen(provider_request, timeout=request.timeout_seconds) as response:
                status = response.getcode()
            is_success = 200 <= status < 300
            detail = "Connection succeeded." if is_success else "Provider returned an error."
            return _result(request, started, is_success, detail)
        except HTTPError as error:
            return _result(request, started, False, f"Provider returned HTTP {error.code}.")
        except (URLError, TimeoutError, OSError):
            return _result(request, started, False, "Provider connection failed.")


def _provider_request(request: ConnectionCheckRequest) -> Request:
    secret = request.secret.get_secret_value() if request.secret is not None else None
    if request.provider is Provider.OPENAI:
        return Request(
            f"https://api.openai.com/v1/models/{quote(request.target, safe='')}",
            headers={"Authorization": f"Bearer {secret}", "User-Agent": _USER_AGENT},
        )
    if request.provider is Provider.GOOGLE_GEMINI:
        query = urlencode({"key": secret})
        return Request(
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{quote(request.target, safe='')}?{query}",
            headers={"User-Agent": _USER_AGENT},
        )
    if request.provider is Provider.AZURE_OPENAI:
        return _azure_request(request, secret)
    revision = quote(request.revision or "main", safe="")
    model = quote(request.target, safe="/")
    headers = {"User-Agent": _USER_AGENT}
    if secret:
        headers["Authorization"] = f"Bearer {secret}"
    return Request(
        f"https://huggingface.co/{model}/resolve/{revision}/config.json",
        headers=headers,
        method="HEAD",
    )


def _azure_request(request: ConnectionCheckRequest, secret: str | None) -> Request:
    if request.endpoint is None or secret is None:
        raise ValueError("Validated Azure settings and credentials are required.")
    deployment = quote(request.target, safe="")
    if request.capability is Capability.EMBEDDING:
        operation = "embeddings"
        payload: dict[str, object] = {"input": "."}
    else:
        operation = "chat/completions"
        payload = {
            "messages": [{"role": "user", "content": "Reply OK."}],
            "max_completion_tokens": 1,
        }
    url = (
        f"{request.endpoint.rstrip('/')}/openai/deployments/{deployment}/{operation}"
        f"?api-version={_AZURE_API_VERSION}"
    )
    return Request(
        url,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
        headers={
            "api-key": secret,
            "Content-Type": "application/json",
            "User-Agent": _USER_AGENT,
        },
        method="POST",
    )


def _result(
    request: ConnectionCheckRequest,
    started: float,
    is_success: bool,
    detail: str,
) -> ConnectionCheckResult:
    return ConnectionCheckResult(
        provider=request.provider,
        capability=request.capability,
        target=request.target,
        is_success=is_success,
        latency_ms=max(0, round((monotonic() - started) * 1000)),
        detail=detail,
    )
