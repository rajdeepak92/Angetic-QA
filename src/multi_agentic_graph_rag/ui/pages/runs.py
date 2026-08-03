"""Runs page."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    """Render the run-history shell."""
    st.title("Runs")
    st.info("No workflow runs are available yet.")
