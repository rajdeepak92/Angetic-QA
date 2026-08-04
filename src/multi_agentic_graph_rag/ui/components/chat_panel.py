"""Native Streamlit chat rendering for the Workbench."""

from __future__ import annotations

import streamlit as st

from multi_agentic_graph_rag.ui.state.session import (
    WORKBENCH_CHAT_INPUT_KEY,
    ConversationMessage,
)


def render_chat_messages(messages: tuple[ConversationMessage, ...]) -> None:
    """Render session conversation messages in chronological order."""
    st.subheader("Conversation")
    if not messages:
        st.info('Try: Generate user stories from "C:\\Documents\\BRD_SRS_DOC.pdf"')
    for message in messages:
        with st.chat_message(message.role):
            st.write(message.content)


def chat_input() -> str | None:
    """Render the bottom composer and return submitted command text."""
    return st.chat_input(
        'Generate user stories from "C:\\Documents\\BRD_SRS_DOC.pdf"',
        key=WORKBENCH_CHAT_INPUT_KEY,
    )
