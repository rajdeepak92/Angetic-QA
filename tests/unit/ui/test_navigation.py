"""Streamlit shell tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = Path("src/multi_agentic_graph_rag/ui/app.py")


def test_app_default_page_renders_workbench() -> None:
    """The application starts on the Workbench without an exception."""
    app = AppTest.from_file(APP_PATH).run(timeout=10)

    assert not app.exception
    assert app.title[0].value == "Workbench"


@pytest.mark.parametrize(
    ("module", "title", "needs_context"),
    [
        ("workbench", "Workbench", True),
        ("runs", "Runs", False),
        ("settings", "Settings", True),
        ("health", "System Health", True),
    ],
)
def test_navigation_page_renders(module: str, title: str, needs_context: bool) -> None:
    """Each declared navigation destination renders its accessible title."""
    context = (
        "from multi_agentic_graph_rag.bootstrap import build_app_context\n" if needs_context else ""
    )
    argument = "build_app_context()" if needs_context else ""
    script = (
        f"{context}from multi_agentic_graph_rag.ui.pages.{module} import render\nrender({argument})"
    )
    app = AppTest.from_string(script).run(timeout=10)

    assert not app.exception
    assert app.title[0].value == title
