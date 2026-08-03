"""Settings page."""

from __future__ import annotations

import streamlit as st


def render() -> None:
    """Render the settings shell."""
    st.title("Settings")
    st.info("Provider and model settings will be enabled in F-002.")
