"""Streamlit shell tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = Path("src/multi_agentic_graph_rag/ui/app.py")


def test_app_default_page_renders_workbench() -> None:
    """The application starts on the Workbench without an exception."""
    app = AppTest.from_file(APP_PATH).run()

    assert not app.exception
    assert app.title[0].value == "Workbench"


@pytest.mark.parametrize(
    ("module", "title"),
    [
        ("workbench", "Workbench"),
        ("runs", "Runs"),
        ("settings", "Settings"),
        ("health", "System Health"),
    ],
)
def test_navigation_page_renders(module: str, title: str) -> None:
    """Each declared navigation destination renders its accessible title."""
    script = f"from multi_agentic_graph_rag.ui.pages.{module} import render\nrender()"
    app = AppTest.from_string(script).run()

    assert not app.exception
    assert app.title[0].value == title
