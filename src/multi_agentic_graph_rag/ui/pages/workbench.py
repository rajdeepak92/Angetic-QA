"""Workbench page."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    """Render the workflow workbench shell."""
    st.title("Workbench")
    st.info("Workflow execution will be enabled by the staged product features.")
