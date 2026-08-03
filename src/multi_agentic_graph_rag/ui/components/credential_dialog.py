"""Batched native Streamlit credential dialog."""

from __future__ import annotations

import streamlit as st

from multi_agentic_graph_rag.domain.enums import Provider
from multi_agentic_graph_rag.ui.state.credentials import store_provider_secrets
from multi_agentic_graph_rag.ui.state.session import CREDENTIAL_FORM_KEY, credential_widget_key


@st.dialog("Provider credentials", icon=":material/key:")
def render_credential_dialog(providers: tuple[Provider, ...]) -> None:
    """Collect one password value for each unique provider in one form."""
    st.caption("Credentials stay in this browser session and are never written by the application.")
    with st.form(CREDENTIAL_FORM_KEY, clear_on_submit=True):
        submitted_values = {
            provider: st.text_input(
                f"{provider.display_name} credential",
                type="password",
                key=credential_widget_key(provider.value),
            )
            for provider in providers
        }
        submitted = st.form_submit_button("Use for this session", type="primary")

    if submitted:
        if any(not value for value in submitted_values.values()):
            st.error("Enter every requested provider credential.")
            return
        store_provider_secrets(submitted_values)
        st.success("Credentials stored for this session. Close this dialog to continue.")
