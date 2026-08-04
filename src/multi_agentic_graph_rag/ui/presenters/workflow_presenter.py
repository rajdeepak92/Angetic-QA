"""Map workflow state into Streamlit-friendly view values."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

from multi_agentic_graph_rag.domain.enums import RunStatus
from multi_agentic_graph_rag.workflows.events import (
    WORKFLOW_STAGES,
    WorkflowEvent,
    WorkflowNodeState,
    WorkflowRunSnapshot,
    WorkflowStage,
)


@dataclass(frozen=True, slots=True)
class StageView:
    """One workflow stage as displayed in the UI."""

    stage: WorkflowStage
    label: str
    state: WorkflowNodeState
    state_label: str


def stage_views(run: WorkflowRunSnapshot | None) -> tuple[StageView, ...]:
    """Return every stage, preserving canonical workflow order."""
    states = (
        {item.stage: item.state for item in run.stage_states}
        if run is not None
        else dict.fromkeys(WORKFLOW_STAGES, WorkflowNodeState.PENDING)
    )
    return tuple(
        StageView(
            stage=stage,
            label=stage.label,
            state=states[stage],
            state_label=states[stage].value.upper(),
        )
        for stage in WORKFLOW_STAGES
    )


def mermaid_diagram(run: WorkflowRunSnapshot | None) -> str:
    """Build a Mermaid diagram whose labels include non-color state text."""
    views = stage_views(run)
    node_lines = [
        f'    {view.stage.value}["{view.label}<br/>{view.state_label}"]:::{view.state.value}'
        for view in views
    ]
    edge_lines = [
        f"    {left.stage.value} --> {right.stage.value}" for left, right in pairwise(views)
    ]
    class_lines = [
        "    classDef pending fill:#f7f7f7,stroke:#6b7280,color:#111827;",
        "    classDef ready fill:#e0f2fe,stroke:#0369a1,color:#0c4a6e;",
        "    classDef running fill:#fef9c3,stroke:#a16207,color:#713f12;",
        "    classDef succeeded fill:#dcfce7,stroke:#15803d,color:#14532d;",
        "    classDef failed fill:#fee2e2,stroke:#b91c1c,color:#7f1d1d;",
        "    classDef blocked fill:#ffedd5,stroke:#c2410c,color:#7c2d12;",
        "    classDef skipped fill:#f3f4f6,stroke:#9ca3af,color:#374151;",
    ]
    return "\n".join(("flowchart LR", *node_lines, *edge_lines, *class_lines))


def latest_event(run: WorkflowRunSnapshot | None) -> WorkflowEvent | None:
    """Return the most recent emitted event, if any."""
    return run.events[-1] if run is not None and run.events else None


def status_label(status: RunStatus) -> str:
    """Return a user-facing run status label."""
    return status.value.replace("_", " ").upper()


def states_table(run: WorkflowRunSnapshot | None) -> list[dict[str, str]]:
    """Return stage rows suitable for Streamlit tables."""
    return [{"Stage": view.label, "State": view.state_label} for view in stage_views(run)]
