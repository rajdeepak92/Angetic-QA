"""Runs page."""

from __future__ import annotations

import streamlit as st

from multi_agentic_graph_rag.ui.state.session import (
    RUNS_PROJECT_FILTER_KEY,
    RUNS_STATUS_FILTER_KEY,
    workflow_runs,
)


def render() -> None:
    """Render the run-history shell."""
    st.title("Runs")
    runs = workflow_runs()
    project_filter = st.text_input("Project filter", key=RUNS_PROJECT_FILTER_KEY)
    status_filter = st.text_input("Status filter", key=RUNS_STATUS_FILTER_KEY)
    filtered = tuple(
        run
        for run in runs
        if project_filter in str(run.request.project_id)
        and status_filter.casefold() in run.status.value.casefold()
    )
    if not filtered:
        st.info("No workflow runs are available for the current filters.")
        return
    st.table(
        [
            {
                "Project ID": str(run.request.project_id),
                "Run ID": str(run.request.run_id),
                "Target": run.request.target_stage.value.replace("_", " ").title(),
                "Status": run.status.value.upper(),
                "Created": run.created_at.isoformat(),
                "Updated": run.updated_at.isoformat(),
                "Error": run.events[-1].error_summary or "None",
                "Resumable": "No checkpoint yet",
                "Lineage": str(run.request.source.resolved_path),
                "Artifacts": "None",
            }
            for run in filtered
        ]
    )
