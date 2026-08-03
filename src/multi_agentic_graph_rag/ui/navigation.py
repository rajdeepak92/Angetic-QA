"""Top-level Streamlit navigation."""

from __future__ import annotations

from functools import partial

import streamlit as st

from multi_agentic_graph_rag.bootstrap import AppContext
from multi_agentic_graph_rag.ui.pages import health, runs, settings, workbench


def run_navigation(context: AppContext) -> None:
    """Render and run the four-page product navigation."""
    pages = [
        st.Page(
            workbench.render,
            title="Workbench",
            icon=":material/work:",
            url_path="workbench",
            default=True,
        ),
        st.Page(runs.render, title="Runs", icon=":material/history:", url_path="runs"),
        st.Page(
            partial(settings.render, context),
            title="Settings",
            icon=":material/settings:",
            url_path="settings",
        ),
        st.Page(
            partial(health.render, context),
            title="System Health",
            icon=":material/monitor_heart:",
            url_path="system-health",
        ),
    ]
    st.navigation(pages, position="top").run()
