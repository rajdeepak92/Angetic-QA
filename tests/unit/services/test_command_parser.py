"""Command-parser tests for the F-004 chat surface."""

from __future__ import annotations

import pytest

from multi_agentic_graph_rag.domain.enums import TargetStage
from multi_agentic_graph_rag.domain.errors import DomainValidationError
from multi_agentic_graph_rag.services.command_parser import (
    SUPPORTED_COMMAND_HELP,
    parse_chat_command,
)


def test_parse_chat_command_accepts_supported_phrases() -> None:
    """Supported command text maps to the intended target stage and path."""
    parsed = parse_chat_command('Generate user stories from "C:\\Documents\\BRD_SRS_DOC.pdf"')

    assert parsed.target_stage is TargetStage.USER_STORIES
    assert parsed.source_text == "C:\\Documents\\BRD_SRS_DOC.pdf"


@pytest.mark.parametrize(
    ("command_text", "message"),
    [
        ("", "Generate requirements from"),
        (
            "Generate requirements from 'C:\\Documents\\BRD_SRS_DOC.pdf",
            "Document path quotes are incomplete.",
        ),
        ("delete everything", "Generate requirements from"),
        ("x" * 2001, "Generate requirements from"),
    ],
)
def test_parse_chat_command_rejects_unsupported_or_ambiguous_text(
    command_text: str,
    message: str,
) -> None:
    """Unsupported or ambiguous commands fail with a sanitized help message."""
    with pytest.raises(DomainValidationError, match=message):
        parse_chat_command(command_text)

    assert "powershell" not in SUPPORTED_COMMAND_HELP.lower()
