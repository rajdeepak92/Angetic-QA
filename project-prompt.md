# Agentic-QA sequential feature runner

> Operational procedure, not a product or architecture contract.
>
> Keep this file at `D:\Repos\Agentic-QA\project-prompt.md`. The physical repository, Git history,
> and six files in `coding-agent-context/` remain authoritative. This runner covers F-004 through
> F-011, one feature per clean Codex Code session.

## Session contract

- Implement exactly one current `READY` feature in the inclusive range F-004 through F-011.
- F-004 may start only when F-003 is factually `DONE` and physically implemented.
- Start from a clean, human-reviewed, committed worktree. If the worktree is dirty, preserve it,
  report the paths, and stop.
- Never start the next feature in the same session. After a successful feature, mark only that
  feature `DONE`, promote only the next explicitly declared dependency-ready feature to `READY`,
  report, and stop for human review and commit.
- The human starts a fresh Codex Code session and reuses the same invocation for the next feature.
- A failure, `NOT_RUN` mandatory gate, contradiction, missing dependency, or approval boundary stops
  the sequence. Never skip a feature or pre-mark a later feature.
- After F-011 passes, mark F-011 `DONE`; do not promote any feature outside this range unless the
  authoritative contracts explicitly require it. Report the declared next state.

## Authority and scope

- Physical files and Git prove what exists. Planned paths are not implementation evidence.
- These six Markdown files define intended behavior, architecture, layout, standards, workflow,
  feature status, and completion history:

  1. `coding-agent-context/project-overview.md`
  2. `coding-agent-context/project-architecture-stack.md`
  3. `coding-agent-context/layout.md`
  4. `coding-agent-context/coding-standard.md`
  5. `coding-agent-context/ai-workflow-rules.md`
  6. `coding-agent-context/progress-tracker.md`

- This file selects a procedure; it cannot invent or override feature facts.
- Implement the smallest complete vertical slice of the selected feature. Do not scaffold later
  features.
- Stop on a conflict between this file and an authoritative contract and report both exact clauses.

## Mandatory orientation

Read all six authoritative files completely, in the order above. Then inspect:

- `git status --short`, `git rev-parse HEAD`, and relevant committed history;
- the complete physical implementation and tests of all declared dependencies;
- every existing caller, interface, domain type, port, adapter, service, workflow, UI surface,
  configuration, script, store, and infrastructure file affected by the current feature;
- `pyproject.toml`, `uv.lock`, `config.json`, and `.env.example` when relevant;
- required tools, services, listeners, ports, and credential-free test prerequisites;
- every graph- or context-referenced path with `Test-Path` or `Get-Item` before treating it as real.

Preserve all user changes. Do not edit anything until the readiness report passes.

## Graphify boundary

Graphify is query-only and secondary. You may run one scoped navigation query:

```powershell
graphify query `
    "Identify the current READY feature, dependencies, acceptance criteria, owners, callers and tests." `
    --graph ".\graphify-out\graph.json"
```

Verify every result against physical files and the six contracts. Never use `/graphify`, `$graphify`,
`graphify extract`, `update`, `watch`, `merge-graphs`, `cluster-only`, `export`, `hook install`, forced
writes, or manual pruning. Do not edit `graphify-out/` or `Framework-KG/`.

## Readiness gate

Select the single current `READY` feature in F-004 through F-011. Stop if none or more than one is
`READY`, if the previous feature is not `DONE`, or if overview and tracker disagree.

Before editing, report:

1. Feature ID, name, stage, and exact authoritative status.
2. Exact context sections defining it.
3. Completed dependencies and physical evidence.
4. In-scope observable behavior and explicit exclusions.
5. Acceptance criteria mapped to proposed evidence/tests.
6. Existing owners and files to create or modify.
7. Architecture, data, trust, security, persistence, and infrastructure boundaries.
8. Authorized dependency, package, model, runtime, and container-image versions.
9. Required unit, contract, integration, UI, and completion gates.
10. Worktree state, prerequisites, approval boundaries, contradictions, and blockers.

If the gate is consistent and all non-destructive prerequisites exist, implement without waiting for
routine approval. Stop only for a real boundary defined here or in `ai-workflow-rules.md`.

## Implementation rules

- Set only the selected feature to `IN_PROGRESS` when implementation actually begins.
- Follow `layout.md`, `coding-standard.md`, and `project-architecture-stack.md` exactly.
- Reuse existing code, standard library, native platform features, and already-authorized
  dependencies before adding abstractions or packages.
- Keep deterministic IDs, checksums, canonicalization, provenance, validation, and destructive
  target selection outside model calls.
- Apply strict validation at trust boundaries; invalid input or output must fail explicitly.
- Preserve declared domain/port/service/adapter/workflow/composition boundaries.
- Add success, validation, failure, security, and regression tests at the lowest owning layer.
- Default tests must not require provider API keys or paid calls.
- Never persist, print, log, expose, or commit credentials or sensitive source material.
- Do not silently fall back between providers or stores.
- Do not perform Git commits, staging, pushes, pulls, resets, rebases, branch changes, stashes,
  destructive cleanup, OS-wide changes, unapproved external writes, or destructive resets.

## Ponytail and review

Use Ponytail Full while implementing. Before completion, run the project-approved Ponytail Review on
the current diff. Resolve findings that affect scope, duplication, correctness, security, or the
acceptance criteria. Do not weaken behavior or add speculative abstractions to satisfy stylistic
preferences.

## Verification

Run the exact current completion gate from `ai-workflow-rules.md`, including every applicable command:

```powershell
uv lock --check
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q
uv run python -m compileall -q src
& ".\scripts\smoke-ui.ps1"
git diff --check
```

Also run every feature-specific unit, contract, integration, Docker, data, migration, reset-safety,
security, and UI gate required by the current contracts. Report every command as `PASS`, `FAIL`, or
`NOT_RUN` with its actual result. An unavailable, skipped, deselected, or unexecuted mandatory gate is
not a pass.

## Completion transaction

Only after every mandatory gate passes:

1. Update documentation only where owned facts changed.
2. Append exactly one factual record using the next stable `CHG-###` ID; never assume it equals the
   feature number without checking the tracker.
3. Mark only the implemented feature `DONE`.
4. Promote only its next explicitly declared feature to `READY` when every dependency is `DONE`.
5. Leave Git operations and Graphify/Obsidian synchronization to the human.
6. Stop. Do not begin the newly promoted feature in this session.

If a mandatory gate fails or cannot run, do not append a success record, do not mark the feature
`DONE`, and do not promote the next feature. Leave an accurate blocker.

## Required final report

Return:

- implemented feature and final status, or exact blocker;
- changed and created files;
- acceptance-criterion-to-evidence mapping;
- important architecture, data, persistence, security, and boundary decisions;
- dependencies added or removed and why;
- every validation command and exact result;
- Ponytail Review findings and resolutions;
- exact documentation and tracker changes;
- runtime/container/service state and manual start, health, stop, and safe-reset commands when relevant;
- `git status --short` and confirmation that the agent performed no Git mutation;
- the next explicitly declared feature/status or blocker;
- the exact next-session invocation;
- `Graphify synchronization: deferred; canonical graph preserved`.
