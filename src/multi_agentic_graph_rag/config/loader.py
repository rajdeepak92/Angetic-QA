"""Resolve strict settings and environment credentials without reading dotenv files."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

from pydantic import SecretStr

from multi_agentic_graph_rag.config.settings import (
    AppSettings,
    CredentialBundle,
    ModelSelection,
    ProviderCredential,
)
from multi_agentic_graph_rag.domain.enums import Provider, RerankerDevice

_CREDENTIAL_ENVIRONMENT_NAMES = {
    Provider.OPENAI: "OPENAI_API_KEY",
    Provider.GOOGLE_GEMINI: "GOOGLE_API_KEY",
    Provider.AZURE_OPENAI: "AZURE_OPENAI_API_KEY",
    Provider.HUGGING_FACE: "HF_TOKEN",
}


def load_settings(
    config_path: Path,
    *,
    environment: Mapping[str, str] | None = None,
    session_settings: AppSettings | None = None,
) -> AppSettings:
    """Resolve session settings over OS environment over tracked JSON defaults."""
    if session_settings is not None:
        return session_settings

    base = AppSettings.model_validate_json(config_path.read_text(encoding="utf-8"))
    values = os.environ if environment is None else environment
    reasoning_provider = _provider(values.get("MAGR_REASONING_PROVIDER"), base.reasoning.provider)
    embedding_provider = _provider(values.get("MAGR_EMBEDDING_PROVIDER"), base.embedding.provider)

    return AppSettings(
        reasoning=ModelSelection(
            provider=reasoning_provider,
            model=_selection_model(
                values,
                provider=reasoning_provider,
                model_name="MAGR_REASONING_MODEL",
                azure_name="AZURE_OPENAI_REASONING_DEPLOYMENT",
                default=base.reasoning.model,
            ),
        ),
        embedding=ModelSelection(
            provider=embedding_provider,
            model=_selection_model(
                values,
                provider=embedding_provider,
                model_name="MAGR_EMBEDDING_MODEL",
                azure_name="AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
                default=base.embedding.model,
            ),
        ),
        reranking=ModelSelection(
            provider=Provider.HUGGING_FACE,
            model=values.get("MAGR_RERANKING_MODEL", base.reranking.model),
        ),
        reranker_revision=values.get("MAGR_RERANKER_REVISION", base.reranker_revision),
        reranker_device=RerankerDevice(
            values.get("MAGR_RERANKER_DEVICE", base.reranker_device.value)
        ),
        reranker_offline_mode=_boolean(
            values.get("MAGR_RERANKER_OFFLINE_MODE"), base.reranker_offline_mode
        ),
        azure_endpoint=values.get("AZURE_OPENAI_ENDPOINT", base.azure_endpoint),
        document_root=Path(values.get("MAGR_DOCUMENT_ROOT", str(base.document_root))),
        generated_root=Path(values.get("MAGR_GENERATED_ROOT", str(base.generated_root))),
        runtime_root=Path(values.get("MAGR_RUNTIME_ROOT", str(base.runtime_root))),
        connection_timeout_seconds=_integer(
            values.get("MAGR_CONNECTION_TIMEOUT_SECONDS"), base.connection_timeout_seconds
        ),
    )


def load_environment_credentials(
    environment: Mapping[str, str] | None = None,
) -> CredentialBundle:
    """Load provider secrets from the process environment into a redacted bundle."""
    values = os.environ if environment is None else environment
    credentials = tuple(
        ProviderCredential(provider=provider, secret=SecretStr(secret))
        for provider, name in _CREDENTIAL_ENVIRONMENT_NAMES.items()
        if (secret := values.get(name))
    )
    return CredentialBundle(credentials=credentials)


def _provider(value: str | None, default: Provider) -> Provider:
    return default if value is None else Provider(value)


def _selection_model(
    environment: Mapping[str, str],
    *,
    provider: Provider,
    model_name: str,
    azure_name: str,
    default: str,
) -> str:
    if provider is Provider.AZURE_OPENAI:
        return environment.get(azure_name, environment.get(model_name, default))
    return environment.get(model_name, default)


def _boolean(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    if value == "true":
        return True
    if value == "false":
        return False
    raise ValueError("Boolean environment settings must be exactly 'true' or 'false'.")


def _integer(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as error:
        raise ValueError("Integer environment setting is invalid.") from error
