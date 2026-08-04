"""Streamlit Settings and System Health behavior tests."""

from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

from multi_agentic_graph_rag.config.settings import CredentialBundle
from multi_agentic_graph_rag.domain.enums import Provider

SETTINGS_SCRIPT = """
from multi_agentic_graph_rag.bootstrap import build_app_context
from multi_agentic_graph_rag.ui.pages.settings import render
render(build_app_context())
"""

_ENVIRONMENT_NAMES = (
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "HF_TOKEN",
    "MAGR_REASONING_PROVIDER",
    "MAGR_REASONING_MODEL",
    "MAGR_EMBEDDING_PROVIDER",
    "MAGR_EMBEDDING_MODEL",
)


@pytest.fixture(autouse=True)
def _clear_provider_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _ENVIRONMENT_NAMES:
        monkeypatch.delenv(name, raising=False)


def test_settings_shared_provider_prompts_for_one_credential() -> None:
    """Default OpenAI reasoning and embedding render one password field."""
    app = AppTest.from_string(SETTINGS_SCRIPT).run(timeout=10)
    _button(app, "Apply settings").click().run(timeout=10)

    assert not app.exception
    assert [item.label for item in app.text_input if "credential" in item.label] == [
        "OpenAI credential"
    ]


def test_settings_different_providers_prompt_separately() -> None:
    """Different reasoning and embedding providers remain isolated in one dialog."""
    app = AppTest.from_string(SETTINGS_SCRIPT).run(timeout=10)
    embedding_provider = next(item for item in app.selectbox if item.label == "Embedding provider")
    embedding_provider.set_value(Provider.GOOGLE_GEMINI).run(timeout=10)
    _button(app, "Apply settings").click().run(timeout=10)

    credential_labels = [item.label for item in app.text_input if "credential" in item.label]
    assert credential_labels == [
        "Google Gemini credential",
        "OpenAI credential",
    ]


def test_clear_session_credentials_removes_secret_and_results() -> None:
    """The clear action replaces secret-bearing session values with an empty bundle."""
    secret = "ui-test-secret"
    script = f"""
import streamlit as st
from multi_agentic_graph_rag.bootstrap import build_app_context
from multi_agentic_graph_rag.config.settings import CredentialBundle
from multi_agentic_graph_rag.domain.enums import Provider
from multi_agentic_graph_rag.ui.pages.settings import render
from multi_agentic_graph_rag.ui.state.session import CREDENTIALS_KEY
if CREDENTIALS_KEY not in st.session_state:
    st.session_state[CREDENTIALS_KEY] = CredentialBundle().with_secret(Provider.OPENAI, {secret!r})
    st.session_state["magr.credential_input.openai"] = {secret!r}
render(build_app_context())
"""
    app = AppTest.from_string(script).run(timeout=10)
    assert secret not in repr(app.session_state.filtered_state["magr.credentials"])

    _button(app, "Clear session credentials").click().run(timeout=10)
    bundle = app.session_state.filtered_state["magr.credentials"]

    assert isinstance(bundle, CredentialBundle)
    assert bundle.credentials == ()
    assert app.session_state.filtered_state["magr.connection_results"] == ()
    assert "magr.credential_input.openai" not in app.session_state.filtered_state
    assert secret not in repr(app.session_state.filtered_state)


def test_system_health_renders_without_live_connections() -> None:
    """Health rendering reports selected dependencies without making network calls."""
    script = """
from multi_agentic_graph_rag.bootstrap import build_app_context
from multi_agentic_graph_rag.ui.pages.health import render
render(build_app_context())
"""
    app = AppTest.from_string(script).run(timeout=10)

    assert not app.exception
    assert app.title[0].value == "System Health"
    assert any("bounded and sanitized" in item.value for item in app.caption)


def _button(app: AppTest, label: str):
    return next(item for item in app.button if item.label == label)
