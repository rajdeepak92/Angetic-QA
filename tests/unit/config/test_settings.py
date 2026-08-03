"""Strict model catalog, settings, and credential tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from multi_agentic_graph_rag.config.loader import load_environment_credentials, load_settings
from multi_agentic_graph_rag.config.model_catalog import providers_for
from multi_agentic_graph_rag.config.settings import AppSettings, ModelSelection
from multi_agentic_graph_rag.domain.enums import Capability, Provider

CONFIG_PATH = Path("config.json")


def test_catalog_exposes_only_approved_provider_capabilities() -> None:
    """Provider choices remain capability-specific."""
    assert providers_for(Capability.REASONING) == (
        Provider.OPENAI,
        Provider.GOOGLE_GEMINI,
        Provider.AZURE_OPENAI,
    )
    assert providers_for(Capability.RERANKING) == (Provider.HUGGING_FACE,)


def test_settings_reject_extra_and_cross_capability_values() -> None:
    """JSON extras and invalid provider/model combinations fail at the boundary."""
    payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        AppSettings.model_validate_json(json.dumps(payload))

    settings = load_settings(CONFIG_PATH, environment={})
    values = {name: getattr(settings, name) for name in type(settings).model_fields}
    values["reasoning"] = ModelSelection(
        provider=Provider.HUGGING_FACE,
        model="BAAI/bge-reranker-base",
    )
    with pytest.raises(ValidationError, match="does not support reasoning"):
        AppSettings(**values)


def test_azure_requires_a_safe_https_endpoint() -> None:
    """Azure deployment aliases cannot be used without a credential-free HTTPS origin."""
    settings = load_settings(CONFIG_PATH, environment={})
    values = {name: getattr(settings, name) for name in type(settings).model_fields}
    values["reasoning"] = ModelSelection(
        provider=Provider.AZURE_OPENAI,
        model="reasoning-deployment",
    )
    values["azure_endpoint"] = "http://user:secret@example.com?key=value"

    with pytest.raises(ValidationError, match="credential-free HTTPS origin"):
        AppSettings(**values)


def test_loader_precedence_and_unique_provider_credentials() -> None:
    """Session overrides environment, while shared providers require one credential."""
    environment = {
        "MAGR_REASONING_PROVIDER": "google_gemini",
        "MAGR_REASONING_MODEL": "gemini-2.5-pro",
        "MAGR_EMBEDDING_PROVIDER": "google_gemini",
        "MAGR_EMBEDDING_MODEL": "gemini-embedding-2",
    }
    resolved = load_settings(CONFIG_PATH, environment=environment)

    assert resolved.reasoning.model == "gemini-2.5-pro"
    assert resolved.required_credential_providers() == (Provider.GOOGLE_GEMINI,)
    assert load_settings(CONFIG_PATH, environment={}, session_settings=resolved) is resolved


def test_loader_rejects_ambiguous_environment_boolean() -> None:
    """Environment booleans require an exact non-coerced representation."""
    with pytest.raises(ValueError, match="exactly 'true' or 'false'"):
        load_settings(CONFIG_PATH, environment={"MAGR_RERANKER_OFFLINE_MODE": "1"})


def test_environment_credentials_are_redacted_and_never_written(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Loading credentials returns only a redacted in-memory bundle."""
    secret = "test-only-super-secret"
    monkeypatch.chdir(tmp_path)
    bundle = load_environment_credentials({"OPENAI_API_KEY": secret})

    assert bundle.secret_for(Provider.OPENAI) is not None
    assert secret not in repr(bundle)
    assert list(tmp_path.iterdir()) == []
