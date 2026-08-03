"""Strict non-secret settings and session credential contracts."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator, model_validator

from multi_agentic_graph_rag.config.model_catalog import validate_model
from multi_agentic_graph_rag.domain.enums import Capability, Provider, RerankerDevice

STRICT_MODEL_CONFIG = ConfigDict(
    strict=True,
    extra="forbid",
    frozen=True,
    validate_default=True,
)


class ModelSelection(BaseModel):
    """One validated provider and model or deployment selection."""

    model_config = STRICT_MODEL_CONFIG

    provider: Provider
    model: str = Field(min_length=1, max_length=200)

    @field_validator("model")
    @classmethod
    def reject_surrounding_whitespace(cls, value: str) -> str:
        """Reject ambiguous model and deployment aliases."""
        if value != value.strip():
            raise ValueError("Model or deployment must not contain surrounding whitespace.")
        return value


class AppSettings(BaseModel):
    """Validated non-secret settings resolved for one application session."""

    model_config = STRICT_MODEL_CONFIG

    reasoning: ModelSelection
    embedding: ModelSelection
    reranking: ModelSelection
    reranker_revision: str = Field(min_length=1, max_length=200)
    reranker_device: RerankerDevice
    reranker_offline_mode: bool
    azure_endpoint: str | None = Field(default=None, max_length=500)
    document_root: Path
    generated_root: Path
    runtime_root: Path
    connection_timeout_seconds: int = Field(ge=1, le=60)

    @field_validator("reranker_revision")
    @classmethod
    def reject_blank_revision(cls, value: str) -> str:
        """Reject an ambiguous Hugging Face revision."""
        if value != value.strip():
            raise ValueError("Reranker revision must not contain surrounding whitespace.")
        return value

    @model_validator(mode="after")
    def validate_provider_capabilities(self) -> AppSettings:
        """Validate every model against its capability and Azure requirements."""
        selections = (
            (Capability.REASONING, self.reasoning),
            (Capability.EMBEDDING, self.embedding),
            (Capability.RERANKING, self.reranking),
        )
        for capability, selection in selections:
            validate_model(capability, selection.provider, selection.model)

        if any(
            selection.provider is Provider.AZURE_OPENAI
            for selection in (self.reasoning, self.embedding)
        ):
            _validate_azure_endpoint(self.azure_endpoint)
        return self

    def required_credential_providers(self) -> tuple[Provider, ...]:
        """Return each selected secret-bearing provider exactly once."""
        providers = {
            selection.provider
            for selection in (self.reasoning, self.embedding)
            if selection.provider
            in {Provider.OPENAI, Provider.GOOGLE_GEMINI, Provider.AZURE_OPENAI}
        }
        return tuple(sorted(providers, key=lambda provider: provider.value))


class ProviderCredential(BaseModel):
    """One ephemeral provider secret with a redacted representation."""

    model_config = STRICT_MODEL_CONFIG

    provider: Provider
    secret: SecretStr

    @field_validator("secret")
    @classmethod
    def reject_blank_secret(cls, value: SecretStr) -> SecretStr:
        """Reject an empty credential without exposing it."""
        if not value.get_secret_value():
            raise ValueError("Credential must not be empty.")
        return value


class CredentialBundle(BaseModel):
    """Immutable session-only provider credentials."""

    model_config = STRICT_MODEL_CONFIG

    credentials: tuple[ProviderCredential, ...] = ()

    def secret_for(self, provider: Provider) -> SecretStr | None:
        """Return a provider secret when configured."""
        for credential in self.credentials:
            if credential.provider is provider:
                return credential.secret
        return None

    def with_secret(self, provider: Provider, secret: str) -> CredentialBundle:
        """Return a new bundle with one provider credential replaced."""
        replacement = ProviderCredential(provider=provider, secret=SecretStr(secret))
        kept = tuple(item for item in self.credentials if item.provider is not provider)
        return CredentialBundle(
            credentials=tuple(sorted((*kept, replacement), key=lambda item: item.provider.value))
        )


def _validate_azure_endpoint(endpoint: str | None) -> None:
    if endpoint is None:
        raise ValueError("Azure endpoint is required when Azure OpenAI is selected.")
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Azure endpoint must be a credential-free HTTPS origin.")
