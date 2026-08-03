# GraphRAG Agents — project overview

> Build mode: **GREENFIELD / WINDOWS / LOCAL UI**. This file is the authoritative product scope.
> No product behavior exists until its feature is implemented, tested, and recorded.

Related files: [architecture](./project-architecture-stack.md), [layout](./layout.md),
[AI workflow rules](./ai-workflow-rules.md), and [progress](./progress-tracker.md).

## Human editing contract

- One feature row is one independently verifiable unit. Edit or append one row to change scope.
- Keep feature IDs stable. New features use the next unused `F-###` ID.
- Status is `PLANNED`, `READY`, `IN_PROGRESS`, `BLOCKED`, `DONE`, or `REMOVED`.
- Keep exactly one feature `READY` or `IN_PROGRESS` unless the human explicitly requests parallel work.
- Prefer `REMOVED` over deleting a row. A deleted row is still a removal request in the Git diff.
- An agent implements only the requested `READY` feature and never infers future features.

## Product contract

| Field | Required value |
|---|---|
| Repository | `GraphRAG-Agents` |
| Product | Multi-Agentic QA Knowledge GraphRAG |
| Python package | `multi-agentic-graph-rag` |
| Import package | `multi_agentic_graph_rag` |
| Host | Local Windows machine only |
| User interface | Streamlit multipage web application |
| URL | `http://127.0.0.1:8501` by default |
| Input | PDF or DOCX under the configured local document root |
| Final output | Grounded requirements, user stories, declarative test scenarios, and coverage |
| Run boundary | Every workflow uses explicit `project_id` and `run_id` |

Typer and product CLI commands are not part of the application. The only operational entry point is
the local Streamlit server, started by the project PowerShell script.

## User experience

### Navigation

| Page | Purpose |
|---|---|
| Workbench | Submit a document request, watch execution, inspect evidence, and open artifacts. |
| Runs | View project/run history, statuses, errors, lineage, and resumable runs. |
| Settings | Select providers/models, enter missing credentials, and validate connections. |
| System Health | Check Python, model providers, PostgreSQL, Neo4j, Chroma, document root, and disk paths. |

Use Streamlit top navigation. The app must be readable at common desktop widths, keyboard usable,
and built from native Streamlit elements before any custom HTML/CSS.

### Workbench layout

1. Header: product name, project, run ID, target stage, overall status, and Settings shortcut.
2. Workflow canvas: a dynamic Mermaid diagram above the conversation.
3. Execution area: stage status/details on the left and artifacts/coverage/evidence on the right.
4. Conversation: user and application messages in chronological order.
5. Bottom composer: a persistent chat input with a concrete example.

Example request:

```text
Generate user stories from "C:\Documents\BRD_SRS_DOC.pdf"
```

The chat is a command surface, not an open-ended assistant. A deterministic parser converts supported
phrases into a typed `WorkflowRequest`, shows the resolved action/path, and rejects ambiguity. It must
never execute arbitrary Python, PowerShell, SQL, Cypher, shell text, or model-generated commands.

| Requested result | Required execution |
|---|---|
| Requirements | Stage 1.1 and Stage 1.2 |
| User stories | Stage 1.1, Stage 1.2, retrieval, and Stage 2 |
| Test scenarios | Stage 1.1, Stage 1.2, retrieval, Stage 2, Stage 3, and coverage |

Already-compatible completed stages may resume from verified checkpoints. Later stages are shown as
`SKIPPED` only when they are beyond the requested target, never to hide a failure.

### Workflow visualization

Display `Validate request -> Ingest -> Discover requirements -> Retrieve -> Generate stories ->
Generate scenarios -> Coverage`. Node state is one of `PENDING`, `READY`, `RUNNING`, `SUCCEEDED`,
`FAILED`, `BLOCKED`, or `SKIPPED`. Use consistent accessible labels/colors and never rely on color alone.

The status panel shows timestamp, stage, current activity, attempt, item counts, duration, and sanitized
error summary. It never shows API keys, raw model responses, full prompts, database credentials, or
customer-document content beyond explicitly selected evidence.

## Settings and credentials

| Capability | Initial provider choices | Initial model/deployment behavior |
|---|---|---|
| Reasoning | OpenAI, Google Gemini, Azure OpenAI | Approved model dropdown; Azure uses configured deployment aliases. |
| Embedding | OpenAI, Google Gemini, Azure OpenAI | Approved embedding dropdown; Azure uses configured deployment aliases. |
| Reranking | Hugging Face local | Approved cross-encoder dropdown and explicit CPU/CUDA/auto device. |

- Provider/model combinations are capability-validated; the UI must not offer invalid combinations.
- Applying settings requests one credential set per unique selected provider, not one key per model.
- If reasoning and embedding share a provider, ask once and reuse that credential only for that session.
- If providers differ, show separate password fields in one modal dialog.
- Azure also requires endpoint plus distinct reasoning/embedding deployment aliases.
- Hugging Face asks for a token only when the selected model is private or gated.
- Credentials are session-memory only unless preconfigured through environment variables. They are
  never written to `config.json`, `.env` by the UI, artifacts, checkpoints, caches, or logs.
- Settings must provide `Test connection` and `Clear session credentials` actions.

## Foundations no feature may weaken

- Deterministic UUIDv7 identities, SHA-256 checksums, provenance, and canonicalization stay outside LLMs.
- Pydantic validates every trust boundary strictly with `extra="forbid"`.
- Evidence is verbatim, source-scoped, and never invented or silently repaired.
- PostgreSQL is canonical. Neo4j and Chroma are rebuildable projections; JSON artifacts are immutable.
- Provider choice is explicit and has no silent fallback.
- Retries are bounded and limited to classified transient failures.
- Paths are resolved, restricted to the configured document root, extension/size checked, and project scoped.
- Destructive operations require explicit UI confirmation and exact project/run scope.

## Incremental feature register

| ID | Status | Feature contract | Depends on | Completion evidence |
|---|---|---|---|---|
| F-001 | DONE | Bootstrap the Windows/Python 3.12 repository, `uv`/Hatchling project, enterprise layout, Streamlit 1.60+ shell, top navigation, local `127.0.0.1:8501` configuration, PowerShell setup/run/smoke scripts, README, and quality tools. | — | Fresh machine instructions work; server health, navigation AppTest, smoke script, and full gate pass. |
| F-002 | READY | Implement strict configuration, model catalog, provider capability validation, Settings/System Health pages, per-provider credential dialog, session credential clearing, and connection checks. | F-001 | Valid combinations render; missing unique providers prompt once; secrets are absent from disk/log/cache/checkpoint tests. |
| F-003 | PLANNED | Add domain/run contracts, deterministic IDs/checksums, error taxonomy, Docker Compose PostgreSQL/Neo4j infrastructure, Chroma, typed ports/adapters, health checks, versioned schema setup, and confirmed resets. | F-002 | Store contracts, isolation, schema/readback, health, and destructive-safety tests pass. |
| F-004 | PLANNED | Add deterministic chat-command parsing, document-root path policy, typed workflow requests/events, run coordinator, Workbench conversation, Mermaid state diagram, status panel, Runs page, and unsupported-command errors. | F-003 | Command/path tests and AppTest prove correct target stages, dynamic states, sanitized errors, and no fake execution success. |
| F-005 | PLANNED | Stage 1.1a: parse PDF/DOCX deterministically, normalize content, build the source ledger and bounded chunks, and persist canonical chunk records. | F-004 | Identical bytes yield identical document/chunk IDs, order, provenance, and checksums; UI emits truthful progress. |
| F-006 | PLANNED | Stage 1.1b: embed chunks, write Neo4j `Chunk` and Chroma projections, verify readback, and emit `chunk_manifest.json`. | F-005 | Fingerprint, dimension, manifest allowlist, projection parity, and readback gates pass. |
| F-007 | PLANNED | Stage 1.2: discover per-chunk requirements/entities/relationships/assertion dispositions, validate exact evidence, canonicalize deterministically, persist canonical rows, and project allowlisted relations. | F-006 | Every assertion is discovered or disposed; invalid model output fails; readiness and canonicalization gates pass. |
| F-008 | PLANNED | Implement project/run-isolated hybrid retrieval from canonical context, Neo4j, and Chroma with Hugging Face cross-encoder reranking and bounded context. | F-007 | Ranking, evidence, context-budget, provider/device, and cross-project isolation tests pass. |
| F-009 | PLANNED | Stage 2: generate grounded user stories with Given/When/Then criteria, lineage, resumable progress, immutable artifacts, and complete Workbench presentation. | F-008 | The example chat request completes through Stage 2; stories validate, resume without duplication, and expose artifact/evidence links. |
| F-010 | PLANNED | Stage 3: generate declarative test scenarios and coverage with requirement/story traceability, duplicate/unassigned detection, artifacts, and UI coverage views. | F-009 | Scenario/coverage gates pass; uncovered required items cannot appear successful; Stage 3 is usable entirely through UI. |
| F-011 | PLANNED | Harden the complete UI workflow with durable checkpoints, leases, bounded retries, idempotent resume, sanitized observability, end-to-end fixtures, recovery tests, and release documentation. | F-010 | Browser/session interruption recovery and clean-room Stage 1–3 run pass without secrets or runtime artifacts entering source control. |

After a feature passes, mark it `DONE`, append its verified progress record, and promote only the next
dependency-satisfied feature to `READY`.

## Out of scope for this MVP

- Typer/product CLI, public API, remote hosting, LAN exposure, multi-user authentication, or mobile UI.
- Stage 4, executable test code, test-data binding, patching, Robot dry runs, execution, or reporting.
- General-purpose chatbot behavior, arbitrary command execution, custom frontend framework, or remote workers.
- Model-generated identities, checksums, provenance, evidence, canonical relations, or success defaults.
