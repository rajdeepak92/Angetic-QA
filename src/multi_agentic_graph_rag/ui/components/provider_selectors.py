"""Native Streamlit selectors for strict non-secret provider settings."""

from __future__ import annotations

from typing import cast

import streamlit as st
from pydantic import ValidationError

from multi_agentic_graph_rag.config.model_catalog import catalog_entry, providers_for
from multi_agentic_graph_rag.config.settings import AppSettings, ModelSelection
from multi_agentic_graph_rag.domain.enums import Capability, Provider, RerankerDevice
from multi_agentic_graph_rag.ui.state.session import (
    AZURE_ENDPOINT_KEY,
    CONNECTION_TIMEOUT_KEY,
    EMBEDDING_PROVIDER_KEY,
    REASONING_PROVIDER_KEY,
    RERANKER_DEVICE_KEY,
    RERANKER_OFFLINE_KEY,
    RERANKER_REVISION_KEY,
    SETTINGS_FORM_KEY,
    model_widget_key,
)


def render_provider_selectors(current: AppSettings) -> AppSettings | None:
    """Render capability-safe controls and return submitted settings."""
    reasoning_provider = _provider_selector(
        "Reasoning provider",
        Capability.REASONING,
        current.reasoning.provider,
        REASONING_PROVIDER_KEY,
    )
    embedding_provider = _provider_selector(
        "Embedding provider",
        Capability.EMBEDDING,
        current.embedding.provider,
        EMBEDDING_PROVIDER_KEY,
    )

    with st.form(SETTINGS_FORM_KEY):
        reasoning_model = _model_selector(
            Capability.REASONING, reasoning_provider, current.reasoning
        )
        embedding_model = _model_selector(
            Capability.EMBEDDING, embedding_provider, current.embedding
        )
        reranking_model = _model_selector(
            Capability.RERANKING, Provider.HUGGING_FACE, current.reranking
        )
        reranker_revision = st.text_input(
            "Reranker revision",
            value=current.reranker_revision,
            key=RERANKER_REVISION_KEY,
        )
        reranker_device = st.selectbox(
            "Reranker device",
            tuple(RerankerDevice),
            index=tuple(RerankerDevice).index(current.reranker_device),
            format_func=lambda device: device.value.upper(),
            key=RERANKER_DEVICE_KEY,
        )
        reranker_offline_mode = st.checkbox(
            "Hugging Face offline mode",
            value=current.reranker_offline_mode,
            key=RERANKER_OFFLINE_KEY,
        )
        uses_azure = Provider.AZURE_OPENAI in {reasoning_provider, embedding_provider}
        azure_endpoint = (
            st.text_input(
                "Azure OpenAI endpoint",
                value=current.azure_endpoint or "",
                key=AZURE_ENDPOINT_KEY,
            )
            if uses_azure
            else current.azure_endpoint
        )
        timeout_seconds = st.number_input(
            "Connection timeout (seconds)",
            min_value=1,
            max_value=60,
            value=current.connection_timeout_seconds,
            step=1,
            key=CONNECTION_TIMEOUT_KEY,
        )
        submitted = st.form_submit_button("Apply settings", type="primary")

    if not submitted:
        return None
    # Streamlit returns an option from this non-empty, non-editable enum sequence.
    selected_device = cast(RerankerDevice, reranker_device)
    try:
        return AppSettings(
            reasoning=ModelSelection(provider=reasoning_provider, model=reasoning_model),
            embedding=ModelSelection(provider=embedding_provider, model=embedding_model),
            reranking=ModelSelection(
                provider=Provider.HUGGING_FACE,
                model=reranking_model,
            ),
            reranker_revision=reranker_revision,
            reranker_device=selected_device,
            reranker_offline_mode=reranker_offline_mode,
            azure_endpoint=azure_endpoint or None,
            document_root=current.document_root,
            generated_root=current.generated_root,
            runtime_root=current.runtime_root,
            connection_timeout_seconds=timeout_seconds,
        )
    except (ValidationError, ValueError):
        st.error(
            "Settings are invalid. Review the provider, model, deployment, and endpoint values."
        )
        return None


def _provider_selector(
    label: str,
    capability: Capability,
    current: Provider,
    key: str,
) -> Provider:
    providers = providers_for(capability)
    selected = st.selectbox(
        label,
        providers,
        index=providers.index(current),
        format_func=lambda provider: provider.display_name,
        key=key,
    )
    if selected is None:
        raise RuntimeError(f"{label} has no selection.")
    return selected


def _model_selector(
    capability: Capability,
    provider: Provider,
    current: ModelSelection,
) -> str:
    entry = catalog_entry(capability, provider)
    label = (
        f"{capability.value.title()} deployment"
        if entry.uses_deployment_alias
        else (f"{capability.value.title()} model")
    )
    key = model_widget_key(capability.value, provider.value)
    if entry.uses_deployment_alias:
        return st.text_input(
            label,
            value=current.model if current.provider is provider else "",
            key=key,
        )
    selected_model = current.model if current.provider is provider else entry.default_model
    index = entry.models.index(selected_model) if selected_model in entry.models else 0
    selected = st.selectbox(label, entry.models, index=index, key=key)
    if selected is None:
        raise RuntimeError(f"{label} has no selection.")
    return selected
