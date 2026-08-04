"""Run-coordinator tests for the F-004 workflow boundary."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from multi_agentic_graph_rag.config.settings import AppSettings
from multi_agentic_graph_rag.domain.enums import RunStatus, TargetStage
from multi_agentic_graph_rag.domain.errors import DomainValidationError
from multi_agentic_graph_rag.domain.identifiers import deterministic_uuid7, new_uuid7
from multi_agentic_graph_rag.services.run_coordinator import F005_BLOCKER, RunCoordinator


def test_run_coordinator_submit_blocks_before_ingestion() -> None:
    """A supported command yields a truthful blocked snapshot and no fake success."""
    settings = _settings_with_document_root(Path("config.json"))
    document = settings.document_root / "brief.pdf"
    document.write_text("document body", encoding="utf-8")
    created_at = datetime(2026, 8, 4, 12, 30, tzinfo=UTC)
    run_id = deterministic_uuid7(
        timestamp=created_at,
        namespace="run",
        value={"run": "f004"},
    )
    coordinator = RunCoordinator(clock=lambda: created_at, id_factory=lambda: run_id)
    project_id = new_uuid7()

    snapshot = coordinator.submit(
        'Generate user stories from "brief.pdf"',
        project_id=project_id,
        settings=settings,
    )

    assert snapshot.status is RunStatus.BLOCKED
    assert snapshot.request.project_id == project_id
    assert snapshot.request.run_id == run_id
    assert snapshot.request.target_stage is TargetStage.USER_STORIES
    assert snapshot.request.source.resolved_path == document.resolve()
    assert snapshot.request.source.extension == ".pdf"
    assert snapshot.created_at == created_at
    assert snapshot.updated_at == created_at
    assert snapshot.events[0].activity == "Request and source path validated."
    assert snapshot.events[1].error_summary == F005_BLOCKER
    assert snapshot.events[1].state.value == "blocked"
    assert [stage.state.value for stage in snapshot.stage_states] == [
        "succeeded",
        "blocked",
        "pending",
        "pending",
        "pending",
        "skipped",
        "skipped",
    ]


@pytest.mark.parametrize(
    "command_text",
    [
        'Generate user stories from "bad.txt"',
        "Upload all documents",
    ],
)
def test_run_coordinator_rejects_unsupported_commands(command_text: str) -> None:
    """Unsupported text never reaches execution and stays sanitized."""
    settings = _settings_with_document_root(Path("config.json"))
    coordinator = RunCoordinator()

    with pytest.raises(DomainValidationError):
        coordinator.submit(command_text, project_id=new_uuid7(), settings=settings)


def test_run_coordinator_rejects_injected_command_text() -> None:
    """Shell fragments are not executed and fail as a missing document path."""
    settings = _settings_with_document_root(Path("config.json"))
    coordinator = RunCoordinator()

    with pytest.raises(DomainValidationError, match="not found"):
        coordinator.submit(
            'Generate user stories from "brief.pdf && powershell"',
            project_id=new_uuid7(),
            settings=settings,
        )


def _settings_with_document_root(config_path: Path) -> AppSettings:
    base = AppSettings.model_validate_json(config_path.read_text(encoding="utf-8"))
    document_root = Path("documents/inbox").resolve()
    values = {name: getattr(base, name) for name in type(base).model_fields}
    values.update(document_root=document_root)
    document_root.mkdir(parents=True, exist_ok=True)
    return AppSettings(**values)
