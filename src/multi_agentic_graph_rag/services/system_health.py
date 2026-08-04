"""Build truthful system-health values without performing network calls."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

from multi_agentic_graph_rag.config.settings import AppSettings, CredentialBundle
from multi_agentic_graph_rag.domain.enums import Capability
from multi_agentic_graph_rag.ports.models import ConnectionCheckResult
from multi_agentic_graph_rag.ports.repositories import PersistenceHealthPort


@dataclass(frozen=True, slots=True)
class HealthCheck:
    """One sanitized health item safe for presentation."""

    name: str
    is_ready: bool
    detail: str


def system_health(
    settings: AppSettings,
    credentials: CredentialBundle,
    connection_results: tuple[ConnectionCheckResult, ...] = (),
    persistence_checks: tuple[PersistenceHealthPort, ...] = (),
) -> tuple[HealthCheck, ...]:
    """Return local, provider, and store readiness without exposing credentials."""
    checks = [
        HealthCheck(
            "Python",
            sys.version_info[:2] == (3, 12),
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        ),
        _streamlit_health(),
        _directory_health("Document root", settings.document_root),
        _directory_health("Generated root", settings.generated_root),
        _directory_health("Runtime root", settings.runtime_root),
        _model_cache_health(settings),
    ]
    checks.extend(_provider_health(settings, credentials, connection_results))
    checks.extend(
        HealthCheck(result.name, result.is_ready, result.detail)
        for port in persistence_checks
        for result in (port.check_health(),)
    )
    return tuple(checks)


def _directory_health(name: str, path: Path) -> HealthCheck:
    is_ready = path.is_dir() and os.access(path, os.R_OK | os.W_OK)
    return HealthCheck(name, is_ready, "Ready" if is_ready else "Missing or not readable/writable")


def _streamlit_health() -> HealthCheck:
    installed = version("streamlit")
    major_minor = tuple(int(part) for part in installed.split(".")[:2])
    return HealthCheck("Streamlit", (1, 60) <= major_minor < (2, 0), installed)


def _model_cache_health(settings: AppSettings) -> HealthCheck:
    if not settings.reranker_offline_mode:
        return HealthCheck("Reranker model cache", True, "Online mode; cache is optional")
    cache_root = settings.runtime_root / "model-cache"
    try:
        is_ready = (
            cache_root.is_dir() and os.access(cache_root, os.R_OK) and any(cache_root.iterdir())
        )
    except OSError:
        is_ready = False
    return HealthCheck(
        "Reranker model cache",
        is_ready,
        "Offline cache available" if is_ready else "Offline mode requires a populated cache",
    )


def _provider_health(
    settings: AppSettings,
    credentials: CredentialBundle,
    connection_results: tuple[ConnectionCheckResult, ...],
) -> tuple[HealthCheck, ...]:
    selections = (
        (Capability.REASONING, settings.reasoning),
        (Capability.EMBEDDING, settings.embedding),
        (Capability.RERANKING, settings.reranking),
    )
    result_by_selection = {
        (result.capability, result.provider, result.target): result for result in connection_results
    }
    checks = []
    required = set(settings.required_credential_providers())
    for capability, selection in selections:
        result = result_by_selection.get((capability, selection.provider, selection.model))
        has_credential = (
            selection.provider not in required
            or credentials.secret_for(selection.provider) is not None
        )
        if result is not None:
            checks.append(
                HealthCheck(
                    f"{capability.value.title()} · {selection.provider.display_name}",
                    result.is_success,
                    result.detail,
                )
            )
        else:
            checks.append(
                HealthCheck(
                    f"{capability.value.title()} · {selection.provider.display_name}",
                    has_credential,
                    "Configured; connection not tested"
                    if has_credential
                    else "Session credential required",
                )
            )
    return tuple(checks)
