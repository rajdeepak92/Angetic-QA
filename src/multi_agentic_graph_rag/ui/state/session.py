"""Stable keys and typed non-secret Streamlit session values."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import RFC_4122, UUID

import streamlit as st

from multi_agentic_graph_rag.config.settings import AppSettings
from multi_agentic_graph_rag.domain.identifiers import new_uuid7
from multi_agentic_graph_rag.ports.models import ConnectionCheckResult
from multi_agentic_graph_rag.workflows.events import WorkflowRunSnapshot

SETTINGS_KEY = "magr.settings"
CREDENTIALS_KEY = "magr.credentials"
CONNECTION_RESULTS_KEY = "magr.connection_results"
PROJECT_ID_KEY = "magr.project_id"
WORKFLOW_RUNS_KEY = "magr.workflow_runs"
CONVERSATION_MESSAGES_KEY = "magr.conversation_messages"
SETTINGS_FORM_KEY = "magr.settings.form"
CREDENTIAL_FORM_KEY = "magr.credentials.form"
REASONING_PROVIDER_KEY = "magr.settings.reasoning.provider"
EMBEDDING_PROVIDER_KEY = "magr.settings.embedding.provider"
RERANKER_REVISION_KEY = "magr.settings.reranker.revision"
RERANKER_DEVICE_KEY = "magr.settings.reranker.device"
RERANKER_OFFLINE_KEY = "magr.settings.reranker.offline"
AZURE_ENDPOINT_KEY = "magr.settings.azure.endpoint"
CONNECTION_TIMEOUT_KEY = "magr.settings.connection_timeout"
ENTER_CREDENTIALS_KEY = "magr.credentials.open"
TEST_CONNECTIONS_KEY = "magr.connections.test"
CLEAR_CREDENTIALS_KEY = "magr.credentials.clear"
CREDENTIAL_WIDGET_PREFIX = "magr.credential_input."
WORKBENCH_CHAT_INPUT_KEY = "magr.workbench.chat_input"
RUNS_PROJECT_FILTER_KEY = "magr.runs.project_filter"
RUNS_STATUS_FILTER_KEY = "magr.runs.status_filter"


@dataclass(frozen=True, slots=True)
class ConversationMessage:
    """One session-only Workbench conversation message."""

    role: Literal["user", "assistant"]
    content: str


def model_widget_key(capability: str, provider: str) -> str:
    """Return a stable model widget key for one provider capability."""
    return f"magr.settings.{capability}.model.{provider}"


def credential_widget_key(provider: str) -> str:
    """Return a stable password widget key for one provider."""
    return f"{CREDENTIAL_WIDGET_PREFIX}{provider}"


def current_settings(default: AppSettings) -> AppSettings:
    """Return the validated session selection, initializing it once."""
    if SETTINGS_KEY not in st.session_state:
        st.session_state[SETTINGS_KEY] = default
    value = st.session_state[SETTINGS_KEY]
    if not isinstance(value, AppSettings):
        raise TypeError("Session settings contain an invalid value.")
    return value


def store_settings(settings: AppSettings) -> None:
    """Replace the current non-secret session settings."""
    st.session_state[SETTINGS_KEY] = settings
    st.session_state[CONNECTION_RESULTS_KEY] = ()


def current_project_id() -> UUID:
    """Return one explicit session project identifier."""
    if PROJECT_ID_KEY not in st.session_state:
        st.session_state[PROJECT_ID_KEY] = new_uuid7()
    value = st.session_state[PROJECT_ID_KEY]
    if not isinstance(value, UUID) or value.version != 7 or value.variant != RFC_4122:
        raise TypeError("Session project ID contains an invalid value.")
    return value


def conversation_messages() -> tuple[ConversationMessage, ...]:
    """Return typed Workbench messages stored in this session."""
    value = st.session_state.get(CONVERSATION_MESSAGES_KEY, ())
    if not isinstance(value, tuple) or not all(
        isinstance(item, ConversationMessage) for item in value
    ):
        raise TypeError("Session conversation contains an invalid value.")
    return value


def append_conversation_message(message: ConversationMessage) -> None:
    """Append one typed Workbench message."""
    st.session_state[CONVERSATION_MESSAGES_KEY] = (*conversation_messages(), message)


def workflow_runs() -> tuple[WorkflowRunSnapshot, ...]:
    """Return session-visible workflow runs."""
    value = st.session_state.get(WORKFLOW_RUNS_KEY, ())
    if not isinstance(value, tuple) or not all(
        isinstance(item, WorkflowRunSnapshot) for item in value
    ):
        raise TypeError("Session workflow runs contain an invalid value.")
    return value


def append_workflow_run(run: WorkflowRunSnapshot) -> None:
    """Append one workflow run snapshot to session history."""
    st.session_state[WORKFLOW_RUNS_KEY] = (*workflow_runs(), run)


def connection_results() -> tuple[ConnectionCheckResult, ...]:
    """Return sanitized connection results stored in this session."""
    value = st.session_state.get(CONNECTION_RESULTS_KEY, ())
    if not isinstance(value, tuple) or not all(
        isinstance(item, ConnectionCheckResult) for item in value
    ):
        raise TypeError("Session connection results contain an invalid value.")
    return value


def store_connection_results(results: tuple[ConnectionCheckResult, ...]) -> None:
    """Store sanitized provider results for the Settings and Health pages."""
    st.session_state[CONNECTION_RESULTS_KEY] = results
