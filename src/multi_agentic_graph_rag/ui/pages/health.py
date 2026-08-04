"""System Health page."""

from __future__ import annotations

import streamlit as st

from multi_agentic_graph_rag.bootstrap import AppContext
from multi_agentic_graph_rag.services.system_health import system_health
from multi_agentic_graph_rag.ui.state.credentials import current_credentials
from multi_agentic_graph_rag.ui.state.session import connection_results, current_settings


def render(context: AppContext) -> None:
    """Render truthful local and selected-provider readiness."""
    st.title("System Health")
    checks = system_health(
        current_settings(context.default_settings),
        current_credentials(),
        connection_results(),
        context.persistence_checks,
    )
    st.table(
        [
            {
                "Check": check.name,
                "Status": "Ready" if check.is_ready else "Needs attention",
                "Detail": check.detail,
            }
            for check in checks
        ]
    )
    st.caption("Store failures are bounded and sanitized; credentials are never displayed.")
