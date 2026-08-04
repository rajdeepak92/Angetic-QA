"""Deterministic chat-command parser for the Workbench command surface."""

from __future__ import annotations

import re

from multi_agentic_graph_rag.domain.enums import TargetStage
from multi_agentic_graph_rag.domain.errors import DomainValidationError
from multi_agentic_graph_rag.domain.schemas.commands import ParsedCommand

SUPPORTED_COMMAND_HELP = (
    'Use one of: Generate requirements from "C:\\Documents\\BRD.pdf"; '
    'Generate user stories from "C:\\Documents\\BRD.pdf"; '
    'Generate test scenarios from "C:\\Documents\\BRD.pdf".'
)

_COMMANDS: tuple[tuple[re.Pattern[str], TargetStage], ...] = (
    (
        re.compile(r"^\s*generate\s+requirements\s+from\s+(.+?)\s*$", re.IGNORECASE),
        TargetStage.REQUIREMENTS,
    ),
    (
        re.compile(r"^\s*generate\s+user\s+stories\s+from\s+(.+?)\s*$", re.IGNORECASE),
        TargetStage.USER_STORIES,
    ),
    (
        re.compile(r"^\s*generate\s+test\s+scenarios\s+from\s+(.+?)\s*$", re.IGNORECASE),
        TargetStage.TEST_SCENARIOS,
    ),
)


def parse_chat_command(command_text: str) -> ParsedCommand:
    """Parse one supported command phrase or raise a sanitized validation error."""
    if not command_text or len(command_text) > 2000:
        raise DomainValidationError(SUPPORTED_COMMAND_HELP)
    matches = [
        ParsedCommand(target_stage=target_stage, source_text=_unquote(match.group(1)))
        for pattern, target_stage in _COMMANDS
        if (match := pattern.fullmatch(command_text))
    ]
    if len(matches) != 1:
        raise DomainValidationError(SUPPORTED_COMMAND_HELP)
    return matches[0]


def _unquote(value: str) -> str:
    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {'"', "'"}:
        return stripped[1:-1].strip()
    if stripped.startswith(('"', "'")) or stripped.endswith(('"', "'")):
        raise DomainValidationError("Document path quotes are incomplete.")
    return stripped
