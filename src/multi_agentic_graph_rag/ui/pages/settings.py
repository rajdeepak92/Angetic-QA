"""Provider and model settings page."""

from __future__ import annotations

import streamlit as st

from multi_agentic_graph_rag.bootstrap import AppContext
from multi_agentic_graph_rag.config.settings import AppSettings, CredentialBundle
from multi_agentic_graph_rag.domain.enums import Capability, Provider
from multi_agentic_graph_rag.ports.models import ConnectionCheckRequest, ConnectionCheckResult
from multi_agentic_graph_rag.ui.components.credential_dialog import render_credential_dialog
from multi_agentic_graph_rag.ui.components.provider_selectors import render_provider_selectors
from multi_agentic_graph_rag.ui.state.credentials import (
    clear_credentials,
    current_credentials,
    missing_credential_providers,
)
from multi_agentic_graph_rag.ui.state.session import (
    CLEAR_CREDENTIALS_KEY,
    ENTER_CREDENTIALS_KEY,
    TEST_CONNECTIONS_KEY,
    connection_results,
    current_settings,
    store_connection_results,
    store_settings,
)


def render(context: AppContext) -> None:
    """Render validated model settings and session-only credential actions."""
    st.title("Settings")
    st.caption("Provider choices are capability-validated. Credentials stay in session memory.")

    settings = current_settings(context.default_settings)
    credentials = current_credentials()
    dialog_providers: tuple[Provider, ...] = ()

    updated = render_provider_selectors(settings)
    if updated is not None:
        store_settings(updated)
        settings = updated
        missing = missing_credential_providers(settings, credentials)
        if missing:
            dialog_providers = missing
        else:
            st.success("Session settings applied.")

    credential_column, test_column, clear_column = st.columns(3)
    with credential_column:
        if st.button(
            "Enter or replace credentials",
            key=ENTER_CREDENTIALS_KEY,
            use_container_width=True,
        ):
            dialog_providers = settings.required_credential_providers()
    with test_column:
        if st.button(
            "Test connections",
            key=TEST_CONNECTIONS_KEY,
            use_container_width=True,
        ):
            missing = missing_credential_providers(settings, credentials)
            if missing:
                dialog_providers = missing
            else:
                results = _test_connections(context, settings, credentials)
                store_connection_results(results)
                st.success("Connection checks completed.")
    with clear_column:
        if st.button(
            "Clear session credentials",
            key=CLEAR_CREDENTIALS_KEY,
            use_container_width=True,
        ):
            clear_credentials()
            credentials = current_credentials()
            st.success("Session credentials and connection results cleared.")

    _render_credential_status(settings, credentials)
    _render_connection_results(connection_results())
    if dialog_providers:
        render_credential_dialog(dialog_providers)


def _test_connections(
    context: AppContext,
    settings: AppSettings,
    credentials: CredentialBundle,
) -> tuple[ConnectionCheckResult, ...]:
    selections = (
        (Capability.REASONING, settings.reasoning),
        (Capability.EMBEDDING, settings.embedding),
        (Capability.RERANKING, settings.reranking),
    )
    results = []
    for capability, selection in selections:
        request = ConnectionCheckRequest(
            provider=selection.provider,
            capability=capability,
            target=selection.model,
            secret=credentials.secret_for(selection.provider),
            endpoint=settings.azure_endpoint,
            revision=settings.reranker_revision if capability is Capability.RERANKING else None,
            offline_mode=(
                settings.reranker_offline_mode if capability is Capability.RERANKING else False
            ),
            timeout_seconds=settings.connection_timeout_seconds,
        )
        results.append(context.connection_adapter.check(request))
    return tuple(results)


def _render_credential_status(
    settings: AppSettings,
    credentials: CredentialBundle,
) -> None:
    st.subheader("Credential readiness")
    providers = settings.required_credential_providers()
    if not providers:
        st.info("The selected providers require no credentials.")
        return
    st.table(
        [
            {
                "Provider": provider.display_name,
                "Status": (
                    "Available in this session"
                    if credentials.secret_for(provider) is not None
                    else "Required"
                ),
            }
            for provider in providers
        ]
    )


def _render_connection_results(results: tuple[ConnectionCheckResult, ...]) -> None:
    st.subheader("Connection results")
    if not results:
        st.info("No provider connection checks have run in this session.")
        return
    st.table(
        [
            {
                "Provider": result.provider.display_name,
                "Capability": result.capability.value.title(),
                "Model/deployment": result.target,
                "Status": "Ready" if result.is_success else "Failed",
                "Latency (ms)": result.latency_ms,
                "Detail": result.detail,
            }
            for result in results
        ]
    )
