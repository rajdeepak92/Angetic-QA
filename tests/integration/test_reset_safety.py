"""Project infrastructure reset safety tests."""

from __future__ import annotations

import subprocess

import pytest

pytestmark = pytest.mark.integration


def test_volume_reset_rejects_wrong_project_confirmation() -> None:
    """The reset script fails before Docker mutation when confirmation is wrong."""
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-File",
            "scripts/stop-infra.ps1",
            "-RemoveVolumes",
            "-ConfirmProject",
            "wrong-project",
        ],
        capture_output=True,
        check=False,
        text=True,
    )

    assert result.returncode != 0
    assert "requires -ConfirmProject 'agentic-qa'" in result.stderr
