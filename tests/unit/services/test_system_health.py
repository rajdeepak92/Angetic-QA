"""System-health service tests."""

from __future__ import annotations

from pathlib import Path

from pydantic import SecretStr

from multi_agentic_graph_rag.config.loader import load_settings
from multi_agentic_graph_rag.config.settings import (
    AppSettings,
    CredentialBundle,
    ProviderCredential,
)
from multi_agentic_graph_rag.domain.enums import Capability, Provider
from multi_agentic_graph_rag.ports.models import ConnectionCheckResult
from multi_agentic_graph_rag.services.system_health import system_health


def test_system_health_reports_local_and_provider_readiness(tmp_path: Path) -> None:
    """Missing credentials and a failed probe remain visible as non-ready checks."""
    document_root = tmp_path / "documents"
    generated_root = tmp_path / "generated"
    runtime_root = tmp_path / "runtime"
    for path in (document_root, generated_root, runtime_root):
        path.mkdir()

    base = load_settings(Path("config.json"), environment={})
    values = {name: getattr(base, name) for name in type(base).model_fields}
    values.update(
        document_root=document_root,
        generated_root=generated_root,
        runtime_root=runtime_root,
    )
    settings = AppSettings(**values)
    without_credentials = system_health(settings, CredentialBundle())

    assert all(check.is_ready for check in without_credentials[:6])
    assert [check.is_ready for check in without_credentials[6:]] == [False, False, True]

    credentials = CredentialBundle(
        credentials=(
            ProviderCredential(provider=Provider.OPENAI, secret=SecretStr("session-secret")),
        )
    )
    failed_result = ConnectionCheckResult(
        provider=Provider.OPENAI,
        capability=Capability.REASONING,
        target="gpt-5.6",
        is_success=False,
        latency_ms=12,
        detail="Provider returned HTTP 401.",
    )
    with_result = system_health(settings, credentials, (failed_result,))

    assert not with_result[6].is_ready
    assert with_result[6].detail == "Provider returned HTTP 401."
    assert with_result[7].is_ready
    assert "session-secret" not in repr(with_result)
