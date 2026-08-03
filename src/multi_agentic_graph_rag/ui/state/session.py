"""Stable keys and typed non-secret Streamlit session values."""

from __future__ import annotations

import streamlit as st

from multi_agentic_graph_rag.config.settings import AppSettings
from multi_agentic_graph_rag.ports.models import ConnectionCheckResult

SETTINGS_KEY = "magr.settings"
CREDENTIALS_KEY = "magr.credentials"
CONNECTION_RESULTS_KEY = "magr.connection_results"
SETTINGS_FORM_KEY = "magr.settings.form"
CREDENTIAL_FORM_KEY = "magr.credentials.form"
REASONING_PROVIDER_KEY = "magr.settings.reasoning.provider"
EMBEDDING_PROVIDER_KEY = "magr.settings.embedding.provider"
RERANKER_REVISION_KEY = "magr.settings.reranker.revision"
RERANKER_DEVICE_KEY = "magr.settings.reranker.device"
RERANKER_OFFLINE_KEY = "magr.settings.reranker.offline"
AZURE_ENDPOINT_KEY = "magr.settings.azure.endpoint"
CONNECTION_TIMEOUT_KEY = "magr.settings.connection_timeout"
ENTER_CREDENTIALS_KEY = "magr.credentials.open"
TEST_CONNECTIONS_KEY = "magr.connections.test"
CLEAR_CREDENTIALS_KEY = "magr.credentials.clear"
CREDENTIAL_WIDGET_PREFIX = "magr.credential_input."


def model_widget_key(capability: str, provider: str) -> str:
    """Return a stable model widget key for one provider capability."""
    return f"magr.settings.{capability}.model.{provider}"


def credential_widget_key(provider: str) -> str:
    """Return a stable password widget key for one provider."""
    return f"{CREDENTIAL_WIDGET_PREFIX}{provider}"


def current_settings(default: AppSettings) -> AppSettings:
    """Return the validated session selection, initializing it once."""
    if SETTINGS_KEY not in st.session_state:
        st.session_state[SETTINGS_KEY] = default
    value = st.session_state[SETTINGS_KEY]
    if not isinstance(value, AppSettings):
        raise TypeError("Session settings contain an invalid value.")
    return value


def store_settings(settings: AppSettings) -> None:
    """Replace the current non-secret session settings."""
    st.session_state[SETTINGS_KEY] = settings
    st.session_state[CONNECTION_RESULTS_KEY] = ()


def connection_results() -> tuple[ConnectionCheckResult, ...]:
    """Return sanitized connection results stored in this session."""
    value = st.session_state.get(CONNECTION_RESULTS_KEY, ())
    if not isinstance(value, tuple) or not all(
        isinstance(item, ConnectionCheckResult) for item in value
    ):
        raise TypeError("Session connection results contain an invalid value.")
    return value


def store_connection_results(results: tuple[ConnectionCheckResult, ...]) -> None:
    """Store sanitized provider results for the Settings and Health pages."""
    st.session_state[CONNECTION_RESULTS_KEY] = results
