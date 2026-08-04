"""Strict project and run contract tests."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from multi_agentic_graph_rag.domain.enums import ErrorCategory, RunStatus, TargetStage
from multi_agentic_graph_rag.domain.identifiers import new_uuid7
from multi_agentic_graph_rag.domain.schemas.runs import RunFailure, RunRecord


def test_run_contract_rejects_wrong_identity_time_and_extra_fields() -> None:
    """Trust-boundary values remain strict and explicitly UUIDv7/UTC."""
    now = datetime.now(UTC)
    values = {
        "project_id": new_uuid7(),
        "run_id": new_uuid7(),
        "target_stage": TargetStage.REQUIREMENTS,
        "status": RunStatus.PENDING,
        "created_at": now,
        "updated_at": now,
    }

    with pytest.raises(ValidationError, match="UUIDv7"):
        RunRecord(**(values | {"run_id": uuid4()}))
    with pytest.raises(ValidationError, match="timezone-aware"):
        RunRecord(**(values | {"created_at": now.replace(tzinfo=None)}))
    with pytest.raises(ValidationError, match="Extra inputs"):
        RunRecord(**values, unexpected=True)


def test_failed_run_requires_one_sanitized_classified_failure() -> None:
    """Failure details cannot appear on success or disappear from failure."""
    now = datetime.now(UTC)
    values = {
        "project_id": new_uuid7(),
        "run_id": new_uuid7(),
        "target_stage": TargetStage.USER_STORIES,
        "created_at": now,
        "updated_at": now,
    }
    failure = RunFailure(category=ErrorCategory.INTEGRITY, message="Readback failed.")

    failed = RunRecord(**values, status=RunStatus.FAILED, failure=failure)
    assert failed.failure == failure
    with pytest.raises(ValidationError, match="Only failed runs"):
        RunRecord(**values, status=RunStatus.SUCCEEDED, failure=failure)
