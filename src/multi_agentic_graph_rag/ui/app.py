"""Streamlit application entrypoint."""

from __future__ import annotations

import streamlit as st

from multi_agentic_graph_rag.bootstrap import build_app_context
from multi_agentic_graph_rag.ui.navigation import run_navigation

st.set_page_config(
    page_title="GraphRAG Agents",
    page_icon=":material/account_tree:",
    layout="wide",
)

st.caption("Multi-Agentic QA Knowledge GraphRAG · Local application")
run_navigation(build_app_context())
