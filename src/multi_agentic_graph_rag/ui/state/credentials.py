"""Session-only credential initialization, replacement, and clearing."""

from __future__ import annotations

import streamlit as st

from multi_agentic_graph_rag.config.loader import load_environment_credentials
from multi_agentic_graph_rag.config.settings import AppSettings, CredentialBundle
from multi_agentic_graph_rag.domain.enums import Provider
from multi_agentic_graph_rag.ui.state.session import (
    CONNECTION_RESULTS_KEY,
    CREDENTIALS_KEY,
    credential_widget_key,
)


def current_credentials() -> CredentialBundle:
    """Return session credentials, loading process-environment values once."""
    if CREDENTIALS_KEY not in st.session_state:
        st.session_state[CREDENTIALS_KEY] = load_environment_credentials()
    value = st.session_state[CREDENTIALS_KEY]
    if not isinstance(value, CredentialBundle):
        raise TypeError("Session credentials contain an invalid value.")
    return value


def missing_credential_providers(
    settings: AppSettings,
    credentials: CredentialBundle,
) -> tuple[Provider, ...]:
    """Return each selected provider missing its session credential exactly once."""
    return tuple(
        provider
        for provider in settings.required_credential_providers()
        if credentials.secret_for(provider) is None
    )


def store_provider_secrets(secrets: dict[Provider, str]) -> None:
    """Replace submitted provider secrets in the current session bundle."""
    bundle = current_credentials()
    for provider, secret in secrets.items():
        bundle = bundle.with_secret(provider, secret)
    st.session_state[CREDENTIALS_KEY] = bundle
    st.session_state[CONNECTION_RESULTS_KEY] = ()


def clear_credentials() -> None:
    """Remove session credentials and results without reloading environment values."""
    st.session_state[CREDENTIALS_KEY] = CredentialBundle()
    st.session_state[CONNECTION_RESULTS_KEY] = ()
    for provider in Provider:
        st.session_state.pop(credential_widget_key(provider.value), None)
