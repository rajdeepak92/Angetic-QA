# GraphRAG Agents — progress tracker

> Append-only evidence for the greenfield Streamlit rebuild. Desired behavior belongs in
> [project-overview.md](./project-overview.md); implementation decisions belong in
> [project-architecture-stack.md](./project-architecture-stack.md) and [layout.md](./layout.md).

## Current snapshot

| Field | Value |
|---|---|
| Build mode | `GREENFIELD / WINDOWS / LOCAL UI` |
| Product features | `3 / 11 DONE` |
| Current feature | `F-004 READY` |
| Application entrypoint | `src/multi_agentic_graph_rag/ui/app.py` |
| Last record | `CHG-003` |
| Updated | `2026-08-04T19:29:05+05:30` |

Update this snapshot only after appending a record; never rewrite history to match the snapshot.

## Recording rules

- Append one record for every code-changing attempt, including `PARTIAL`, `BLOCKED`, or `REVERTED`.
- Use ISO 8601 timestamps with `Z` or an explicit UTC offset.
- Use the next stable `CHG-###` ID and matching `F-###` feature.
- Record observed behavior, paths, checks, and tool use; never record intentions as completed facts.
- Never record API keys, tokens, endpoints containing secrets, customer text, prompts, or raw responses.
- Mark a feature `DONE` only when its completion evidence and full gate pass.
- Correct history with a new `CORR-###` record; never delete or rewrite a past record.
- Separate every record with `---`.

## BOOT-000 — UI-first greenfield control plane defined

- Timestamp: `2026-08-03T20:38:25+05:30`
- Feature: `N/A`
- Result: `DOCUMENTATION_ONLY`
- Request: Define the first five Graphify context files for a Windows-local Streamlit build through Stage 3.
- Files: `coding-agent-context/project-overview.md`, `coding-agent-context/progress-tracker.md`,
  `coding-agent-context/project-architecture-stack.md`, `coding-agent-context/ai-workflow-rules.md`, `coding-agent-context/layout.md`
- Product behavior delivered: None; application, environment, databases, providers, and UI are not installed.
- Product decision: Streamlit at `127.0.0.1:8501` replaces Typer/product CLI commands.
- UI decision: Workbench, Runs, Settings, and System Health with chat, Mermaid flow, live status, and artifacts.
- Provider decision: OpenAI/Gemini/Azure OpenAI for reasoning/embedding; Hugging Face local reranker.
- Credential decision: One ephemeral credential set per unique provider; never persisted by the UI.
- Graphify: `NOT_RUN` — run after these five files are copied into the new tracked `coding-agent-context/` folder.
- Ponytail: Contract researched; no production diff existed to review.
- Verification: Cross-file authorities, 11 ordered features, UI/state/security contracts, and layout checked.
- Git: Human-owned; no branch, stage, commit, push, or PR action recorded.

---

## CHG-001 — F-001: bootstrap repository and Streamlit shell

- Timestamp: `2026-08-03T22:55:10+05:30`
- Result: `DONE`
- Request: Bootstrap the Windows/Python 3.12 repository and local Streamlit navigation shell.
- Status: `F-001 READY -> DONE`; `F-002 PLANNED -> READY`
- Graphify before: Query for the current READY feature, stage, dependencies, acceptance criteria,
  architecture boundaries, files, tests, and completion gate.
- Files changed: `.streamlit/config.toml`, `README.md`, `pyproject.toml`, `uv.lock`,
  `scripts/bootstrap.ps1`, `scripts/run-app.ps1`, `scripts/smoke-ui.ps1`,
  `src/multi_agentic_graph_rag/__init__.py`, `src/multi_agentic_graph_rag/ui/__init__.py`,
  `src/multi_agentic_graph_rag/ui/app.py`, `src/multi_agentic_graph_rag/ui/navigation.py`,
  `src/multi_agentic_graph_rag/ui/pages/__init__.py`,
  `src/multi_agentic_graph_rag/ui/pages/{workbench,runs,settings,health}.py`,
  `tests/unit/ui/test_navigation.py`, `coding-agent-context/project-overview.md`, and this tracker.
- UI behavior: Local wide-layout Streamlit shell with top Workbench, Runs, Settings, and System Health
  navigation; Workbench is the default page and future behavior is labeled without fake success.
- Contracts/data: Python `>=3.12,<3.13`, Hatchling `src/` build, locked Streamlit 1.60.0, and local
  `127.0.0.1:8501` server configuration; no product data contract or persistence added.
- Security: CORS/XSRF protections remain enabled; server binds only to loopback; no credential fields,
  secrets, customer documents, caches, or runtime artifacts are persisted.
- Ponytail decision: Reused native Streamlit pages/navigation and uv; added no future layers or dependencies.
- Tests: `tests/unit/ui/test_navigation.py` verifies the default page and all four page render paths.
- Verification: `scripts/bootstrap.ps1 = PASS`; `uv sync --frozen = PASS`;
  `uv run ruff check . = PASS`; `uv run ruff format --check . = PASS`;
  `uv run mypy src = PASS`; `uv run pytest -q = PASS (5 passed)`;
  `uv run python -m compileall -q src = PASS`; `scripts/smoke-ui.ps1 = PASS`.
- Graphify after: `NOT_RUN` — the task explicitly required query-only Graphify use and prohibited updates.
- Documentation: `README.md`, `coding-agent-context/project-overview.md`, and this tracker synchronized.
- Follow-up/blocker: `F-002` is the next explicitly declared READY feature; no blocker.
- Git: `Human-owned`

---

## CHG-002 — F-002: configuration, provider readiness, and health UI

- Timestamp: `2026-08-04T04:37:43+05:30`
- Result: `DONE`
- Request: Implement strict configuration, the approved model catalog, capability validation,
  Settings/System Health pages, unique-provider credential handling, clearing, and connection checks.
- Status: `F-002 READY -> DONE`; `F-003 PLANNED -> READY`
- Graphify before: Read-only canonical query for project contracts, architecture authority, scope,
  stage, and tracker navigation; current feature status was verified from physical Markdown files.
- Files changed: `.env.example`, `config.json`, `README.md`, `pyproject.toml`, `uv.lock`,
  `coding-agent-context/{layout,project-overview,progress-tracker}.md`,
  `src/multi_agentic_graph_rag/{bootstrap.py,adapters/,config/,domain/,ports/,services/}`,
  `src/multi_agentic_graph_rag/ui/{app.py,navigation.py,pages/health.py,pages/settings.py,components/,state/}`,
  `tests/contract/models/test_connection_checks.py`, `tests/unit/config/test_settings.py`,
  `tests/unit/services/test_system_health.py`, and
  `tests/unit/ui/{test_navigation,test_provider_pages}.py`.
- UI behavior: Settings renders capability-safe provider/model/deployment controls, batches missing
  unique-provider password inputs in one native dialog, clears session secrets/results, and runs
  explicit sanitized connection probes; System Health renders local, cache, credential, and last-probe readiness.
- Contracts/data: Strict frozen Pydantic settings with `extra="forbid"`; session settings override OS
  environment values, which override tracked non-secret `config.json`; no canonical store, schema,
  checkpoint, cache, or generated artifact was added.
- Security: Credentials use redacted `SecretStr` values, remain only in Streamlit Session State, are
  never logged/persisted/cached/checkpointed, and password widget keys are removed by explicit clearing;
  provider exceptions and response bodies never reach connection results.
- Ponytail decision: Reused native Streamlit, Pydantic, and stdlib `urllib`; one redundant adapter
  mapping was removed; no provider SDK, compatibility layer, background work, or later-feature scaffold was added.
- Tests: Catalog/capability and strict loader validation; environment/session precedence; credential
  deduplication, redaction, no-write behavior, and clearing; four-provider connection success/failure
  contracts; health readiness; Settings dialog and page AppTests.
- Verification: `uv lock --check = PASS`; `uv sync --locked = PASS`;
  `uv run ruff check . = PASS`; `uv run ruff format --check . = PASS (41 files)`;
  `uv run mypy src = PASS (29 source files)`; `uv run pytest -q = PASS (22 passed)`;
  `uv run python -m compileall -q src = PASS`; `scripts/smoke-ui.ps1 = PASS`.
- Graphify after: `NOT_RUN` — query-only boundary; the canonical graph was preserved because the
  staged Graphify 0.9.32 refresh candidate failed the zero-orphan relationship gate.
- Documentation: `README.md`, `coding-agent-context/layout.md`,
  `coding-agent-context/project-overview.md`, and this tracker synchronized.
- Follow-up/blocker: `F-003` is the next explicitly declared READY feature; no blocker.
- Git: `Human-owned`

---

## CHG-003 — F-003: infrastructure and persistence baseline

- Timestamp: `2026-08-04T19:29:05+05:30`
- Result: `DONE`
- Request: Implement domain/run contracts, deterministic identities/checksums, classified errors,
  canonical PostgreSQL, rebuildable Neo4j/Chroma projections, typed adapters, Compose infrastructure,
  idempotent schema setup, bounded health, confirmed reset safety, and System Health integration.
- Status: `F-003 READY -> DONE`; `F-004 PLANNED -> READY`
- Graphify before: Read-only query for the F-003 contract, dependencies, persistence ownership,
  infrastructure, schema, health, reset, tests, and owned files; every result was verified physically.
- Files changed: `.env.example`, `config.json`, `README.md`, `pyproject.toml`, `uv.lock`,
  `infra/compose.yaml`, `scripts/{start-infra,stop-infra,smoke-ui}.ps1`,
  `src/multi_agentic_graph_rag/{bootstrap.py,config/,domain/,ports/repositories.py,services/system_health.py}`,
  `src/multi_agentic_graph_rag/adapters/persistence/`, `src/multi_agentic_graph_rag/ui/`,
  `tests/{unit/domain,unit/config,unit/services,unit/ui,contract/persistence,integration}/`,
  `coding-agent-context/{project-architecture-stack,project-overview,progress-tracker}.md`.
- UI behavior: System Health now renders sanitized PostgreSQL, Neo4j, and embedded Chroma readiness
  through typed health ports; provider/configuration behavior remains unchanged.
- Contracts/data: Strict UUIDv7 project/run/projection models, canonical UTF-8 JSON SHA-256,
  classified failures, PostgreSQL `agentic_qa` schema with immutable migration checksums, and
  rebuildable Neo4j/Chroma project-scope metadata; PostgreSQL remains canonical.
- Security: Store passwords load only from environment into redacted values; SQL/Cypher is
  parameterized; health failures are bounded/sanitized; host PostgreSQL uses 55432; destructive reset
  requires exact project confirmation plus volume-label and Chroma-path validation.
- Ponytail decision: Kept only F-003 projection-scope metadata, reused native Compose health/wait and
  standard SHA-256/JSON, removed unrequested container restart policies, and added no F-004+ behavior.
- Tests: Deterministic known-vector/validation tests; strict run/error tests; Chroma contract;
  Docker PostgreSQL migration/readback/isolation and Neo4j scope/readback/isolation; denied reset;
  System Health/UI integration; all Docker-backed tests ran without skips in the completion suite.
- Verification: `uv lock --check = PASS`; `uv sync --locked = PASS`;
  `uv run ruff check . = PASS`; `uv run ruff format --check . = PASS (56 files)`;
  `uv run mypy src = PASS (38 source files)`; `uv run pytest -q = PASS (33 passed, 0 skipped)`;
  `uv run python -m compileall -q src = PASS`; `scripts/smoke-ui.ps1 = PASS`;
  `git diff --check = PASS`; Compose config/start/health = PASS; persistence Docker gates = PASS
  (4 passed); PostgreSQL migration ledger = PASS (two ordered migrations, 64-character checksums);
  PostgreSQL 55432, Neo4j 7474/7687, and Chroma readback = PASS; confirmation-denied reset = PASS;
  normal shutdown preserved both named volumes and Chroma data.
- Graphify after: `NOT_RUN` — query-only boundary; synchronization deferred and canonical graph preserved.
- Documentation: `README.md`, `coding-agent-context/project-architecture-stack.md`,
  `coding-agent-context/project-overview.md`, and this tracker synchronized.
- Follow-up/blocker: `F-004` is the next explicitly declared READY feature; no blocker.
- Git: `Human-owned`

---

<!-- Insert each new record immediately above this template; leave the template last. -->

## CHG-### — F-###: concise change title

- Timestamp: `<YYYY-MM-DDTHH:MM:SSZ|±HH:MM>`
- Result: `<DONE|PARTIAL|BLOCKED|REVERTED>`
- Request: `<exact requested behavior>`
- Status: `<old status -> new status>`
- Graphify before: `<query/path/explain or NOT_AVAILABLE with reason>`
- Files changed: `<project-relative paths>`
- UI behavior: `<page/component/input/status/error/artifact result or N/A>`
- Contracts/data: `<schema, provider, store, artifact, migration, or NONE>`
- Security: `<credential/path/redaction/isolation checks or N/A>`
- Ponytail decision: `<reuse/stdlib/native/dependency/minimum new code>`
- Tests: `<paths and added success/failure cases>`
- Verification: `<command = PASS|FAIL|NOT_RUN(reason)>`
- Graphify after: `<update and confirming query or NOT_RUN(reason)>`
- Documentation: `<files synchronized or NONE(reason)>`
- Follow-up/blocker: `<next action or NONE>`
- Git: `Human-owned`

---
