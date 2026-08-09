"""Workbench page."""

from __future__ import annotations

import streamlit as st

from multi_agentic_graph_rag.bootstrap import AppContext
from multi_agentic_graph_rag.domain.errors import ApplicationError
from multi_agentic_graph_rag.ui.components.chat_panel import chat_input, render_chat_messages
from multi_agentic_graph_rag.ui.components.execution_status import (
    render_artifact_panel,
    render_execution_status,
)
from multi_agentic_graph_rag.ui.components.workflow_diagram import render_workflow_diagram
from multi_agentic_graph_rag.ui.state.credentials import current_credentials
from multi_agentic_graph_rag.ui.state.session import (
    ConversationMessage,
    append_conversation_message,
    append_workflow_run,
    conversation_messages,
    current_project_id,
    current_settings,
    workflow_runs,
)


def render(context: AppContext) -> None:
    """Render the workflow workbench shell."""
    st.title("Workbench")
    settings = current_settings(context.default_settings)
    project_id = current_project_id()
    submitted = chat_input()
    if submitted:
        _submit_command(context, submitted)

    runs = workflow_runs()
    current_run = runs[-1] if runs else None
    header = st.columns(5)
    header[0].metric("Product", "GraphRAG Agents")
    header[1].metric("Project", str(project_id))
    header[2].metric("Run ID", str(current_run.request.run_id) if current_run else "None")
    header[3].metric(
        "Target",
        current_run.request.target_stage.value.replace("_", " ").title() if current_run else "None",
    )
    header[4].metric("Status", current_run.status.value.upper() if current_run else "IDLE")
    st.link_button("Settings", "/settings", icon=":material/settings:")
    st.caption(f"Document root: {settings.document_root.resolve()}")

    render_workflow_diagram(current_run)
    status_column, artifact_column = st.columns(2)
    with status_column:
        render_execution_status(current_run)
    with artifact_column:
        render_artifact_panel(current_run)
    render_chat_messages(conversation_messages())


def _submit_command(context: AppContext, command_text: str) -> None:
    append_conversation_message(ConversationMessage(role="user", content=command_text))
    try:
        run = context.run_coordinator.submit(
            command_text,
            project_id=current_project_id(),
            settings=current_settings(context.default_settings),
            credentials=current_credentials(),
        )
    except ApplicationError as error:
        append_conversation_message(
            ConversationMessage(role="assistant", content=error.safe_message)
        )
        return
    append_workflow_run(run)
    append_conversation_message(
        ConversationMessage(
            role="assistant",
            content=(
                f"Accepted {run.request.target_stage.value.replace('_', ' ')} for "
                f"{run.request.source.resolved_path}. "
                + (
                    "Document parsed, chunks embedded, projected to Neo4j and Chroma, and manifest written; "
                    "later stages remain pending."
                    if run.status.value == "running"
                    else "Execution is blocked before ingestion; no success was faked."
                )
            ),
        )
    )
