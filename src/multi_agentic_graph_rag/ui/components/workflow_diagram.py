"""Native Streamlit Mermaid workflow diagram."""

from __future__ import annotations

import streamlit as st

from multi_agentic_graph_rag.ui.presenters.workflow_presenter import mermaid_diagram
from multi_agentic_graph_rag.workflows.events import WorkflowRunSnapshot


def render_workflow_diagram(run: WorkflowRunSnapshot | None) -> None:
    """Render the current workflow stage diagram."""
    st.subheader("Workflow")
    st.mermaid_chart(mermaid_diagram(run))
