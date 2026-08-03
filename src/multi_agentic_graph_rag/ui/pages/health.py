"""System Health page."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    """Render the system-health shell."""
    st.title("System Health")
    st.info("Dependency and provider checks will be enabled in later features.")
