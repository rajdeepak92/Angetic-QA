# AI workflow rules — greenfield GraphRAG Agents

These rules govern the Windows-first Streamlit rebuild using
[Graphify](https://github.com/Graphify-Labs/graphify) for repository navigation and
[Ponytail](https://github.com/DietrichGebert/ponytail) for implementation minimalism.

## Authority and graph-safety contract

The repository files and the six Markdown contracts under `coding-agent-context/` are authoritative.
Graphify is a navigation aid and never proves that a planned file or behavior is implemented.

- Use the canonical graph at `graphify-out/graph.json` only after its provenance and relationship
  integrity gates have passed.
- Before reading, modifying, testing, or reporting a graph-referenced path as implemented, verify the
  physical file with `Test-Path`, `Get-Item`, or the equivalent filesystem operation.
- A graph node may represent planned architecture only when its exact path is written verbatim in an
  authoritative context document. Never report a planned node as existing code.
- If a graph statement conflicts with a physical file or an authoritative Markdown contract, the graph
  is stale or incorrect. Follow the source file/contract and report the conflict.
- During feature implementation, coding agents use Graphify in query-only mode. They must not extract,
  update, cluster, watch, install hooks, export, rebuild, or directly edit generated graph artifacts.
- Keep `graphify-out/`, `Framework-KG/`, and Graphify diagnostics local and excluded from Git.

The permitted query form is:

```powershell
graphify query `
    "Identify the current READY feature, its dependencies, acceptance criteria, owners, callers and tests." `
    --graph ".\graphify-out\graph.json"
```

## Fresh-machine contract

Assume only Windows and PowerShell exist. Before F-001, probe with `Get-Command` for `winget`, `git`,
`uv`, `docker`, and `node`. Do not claim a tool is installed until its version command succeeds.

- If `uv` is absent, stop and ask the human to approve one official installation command:

  ```powershell
  winget install --id=astral-sh.uv -e
  ```

- After uv exists, F-001 uses `uv python install 3.12` and creates the project environment through uv.
- Docker Desktop/WSL2 are required only when F-003 begins. Detect them early, but do not install or
  enable Windows features without explicit human approval.
- Node.js is required for Ponytail lifecycle hooks, not for the Python application.
- Never silently install OS software, change execution policy, enable Windows features, or modify
  machine-wide environment variables.

F-001 must create idempotent `scripts/bootstrap.ps1`, `scripts/run-app.ps1`, and
`scripts/smoke-ui.ps1`. Later features extend scripts only when their accepted scope needs it.

## One-time coding-agent-context/tool setup

These six Markdown files must be tracked by Git and visible to Graphify:

1. `project-overview.md`
2. `project-architecture-stack.md`
3. `layout.md`
4. `coding-standard.md`
5. `ai-workflow-rules.md`
6. `progress-tracker.md`

Verify that none is ignored:

```powershell
$ContextFiles = @(
    "project-overview.md",
    "project-architecture-stack.md",
    "layout.md",
    "coding-standard.md",
    "ai-workflow-rules.md",
    "progress-tracker.md"
)

foreach ($Name in $ContextFiles) {
    git check-ignore -- "coding-agent-context/$Name"

    if ($LASTEXITCODE -eq 0) {
        throw "Authoritative context is ignored: $Name"
    }
}
```

Install Graphify's official `graphifyy` package and the project-scoped skill for the applicable host:

```text
uv tool install graphifyy
Codex:       graphify install --project --platform codex
Claude Code: graphify install --project
```

Install Ponytail:

```text
Codex:
  codex plugin marketplace add DietrichGebert/ponytail
  codex plugin add ponytail@ponytail

Claude Code (two separate prompts):
  /plugin marketplace add DietrichGebert/ponytail
  /plugin install ponytail@ponytail
```

For Codex, review and trust Ponytail's two lifecycle hooks in `/hooks`, then start a new thread. Use
Ponytail `full`.

Only when no validated canonical graph exists, build the initial graph from all six context files and
the current physical codebase. Do not use `--code-only`, because it excludes the semantic Markdown
contracts. Treat the generated graph as untrusted until the provenance and orphan-relationship gates
pass. Do not promote, query as canonical, or export a failed graph.

When a validated canonical graph already exists, do not rebuild it during feature implementation.

## Read in this order

1. [project-overview.md](./project-overview.md) — product behavior and active feature.
2. [project-architecture-stack.md](./project-architecture-stack.md) — runtime and technology contracts.
3. [layout.md](./layout.md) — exact file ownership and dependency direction.
4. [coding-standard.md](./coding-standard.md) — production Python design, typing, validation, logging,
   testing, and maintainability rules.
5. This file — execution, security, documentation, and completion rules.
6. [progress-tracker.md](./progress-tracker.md) — verified history, current state, and blockers.

Then query Graphify for the active feature, related contracts, existing physical owners, callers,
tests, stores, and artifacts. Graphify narrows inspection; read every physical file that will be edited.

## Work from one explicit feature

- Select the single `READY` feature requested by the human. If none is ready or requested, clarify.
- Confirm dependencies are `DONE`, target UI behavior, stage, contracts, trust boundaries, paths, and gate.
- Set `IN_PROGRESS` only when implementation begins.
- Complete one vertical feature with code, failures, tests, docs, and required scripts/configuration.
- Do not scaffold later features, copy a legacy project wholesale, or report planned behavior as present.
- A deleted or `REMOVED` feature is a removal request. Trace dependents and confirm destructive
  data/schema effects before making changes.

## Apply Ponytail safely

Choose the first correct option: remove unnecessary scope, reuse existing code, use the standard
library, use a native platform feature, use an installed dependency, express the behavior directly,
or add the minimum new implementation.

- Codex: use `@ponytail` while implementing and `@ponytail-review` before completion.
- Claude Code: use `/ponytail full` while implementing and `/ponytail-review` before completion.
- Resolve applicable review findings or record a concrete non-applicability reason.

Minimalism may not remove strict validation, evidence fidelity, path safety, deterministic fields,
project/run isolation, credential protection, data-loss handling, checkpointing, accessibility,
observability, failure UX, tests, or accepted behavior.

## Streamlit boundary

- Streamlit pages/components render typed view models and invoke typed application facades only.
- No page/component imports provider SDKs, `psycopg`, Neo4j, Chroma, or document parsers.
- No workflow/service imports Streamlit or writes directly to a Streamlit container.
- `bootstrap.py` is the only composition root and contains wiring, not business logic.
- Use native `st.navigation`, `st.dialog`, `st.form`, `st.chat_*`, `st.status`, and
  `st.mermaid_chart` before new UI dependencies or custom HTML/CSS.
- Do not nest chat-message containers, status containers, or columns beyond Streamlit guidance.
- Bind only to `127.0.0.1:8501`. Do not disable CORS/XSRF or expose the server to LAN/internet.
- Streamlit Session State is presentation/session memory, never canonical workflow state.

## Chat and path safety

- Parse only supported command intents into a strict `WorkflowRequest`; ambiguity returns guidance.
- Never execute user text as Python, shell, PowerShell, SQL, Cypher, template code, or tool input.
- Never let an LLM choose the local path, project ID, run ID, destructive action, or target stage.
- Resolve the path with `Path.resolve(strict=True)`; require a regular `.pdf`/`.docx` file under the
  configured document root, enforce size limits, and reject symlink/path-traversal escape.
- Display the canonical path/action before execution. Destructive resets require a separate
  confirmation dialog.

## Provider and secret safety

- Model options come only from the approved capability catalog; no free-form provider/model execution.
- Azure uses configured deployment aliases and a validated endpoint; never substitute a model ID.
- Prompt once per missing unique provider credential. Same-provider reasoning/embedding may share one
  credential bundle; different providers remain separate.
- Render secret fields with password inputs. Never echo, partially display, log, serialize, cache,
  checkpoint, persist, export, or include credentials in exceptions.
- Do not put credential-bearing clients in `st.cache_data` or `st.cache_resource`.
- Clearing credentials overwrites/removes session keys and provider-client references.
- Connection tests use minimal requests, bounded timeouts, and sanitized results.
- No provider fallback. A selected provider failure remains that provider's explicit failure.

## Workflow and data integrity

- Keep deterministic identities, checksums, canonicalization, provenance, and coverage outside models.
- Keep prompts/model output behind typed ports and strict response models.
- Invalid model output is a failed/repairable model attempt, never empty success.
- Evidence remains verbatim and scoped to supplied chunks/context.
- PostgreSQL remains canonical; Neo4j/Chroma are projections; JSON artifacts are immutable.
- LangGraph state is JSON-serializable and contains no secret/client/full document body.
- Nodes with external calls or writes are idempotent at checkpoint replay boundaries.
- Retry only classified transient errors within configured bounds; unexpected errors surface.

## Tests and verification

- Add tests with the owning feature; test success, validation, security, and failure states.
- Use ports/fakes for unit tests. No live API key is required by the default test suite.
- Use Streamlit `AppTest` for navigation, settings, command, dialog, status, and error UI.
- Contract tests prove each provider/store adapter satisfies its port.
- Integration tests requiring Docker or live providers are explicitly marked and never reported as
  passing when skipped or unavailable.
- Every bug fix adds a regression test at the lowest owning layer.

## Documentation and post-feature synchronization

After implementation is complete and every applicable completion command passes:

1. Update overview scope/status, architecture decisions, layout paths, public README/workflow, or these
   rules only when their owned facts changed.
2. Append one factual `CHG-###` record to `progress-tracker.md`. Never pre-record success.
3. Run Ponytail review and resolve applicable findings.
4. Return the changed-file list, validation evidence, tracker entry, launch command, and next declared
   feature or blocker.
5. Stop before Git mutation or Graphify mutation. The human owns both post-feature operations.

| Change | Required documentation |
|---|---|
| Feature added, changed, or removed | Overview + progress |
| Stack, provider, store, schema, artifact, or server contract | Architecture + progress |
| Directory, file owner, or dependency direction | Layout + progress |
| User-visible UI, configuration, or workflow | README/workflow + progress |
| Agent procedure or quality gate | This file + progress |

### Human-controlled Graphify refresh

After the human has reviewed the staged diff, rerun all completion gates and created a clean commit:

1. Back up the canonical graph, labels, report, HTML, diagnostics, and current Obsidian vault.
2. Use only the repository-approved AST-preserving incremental procedure for the installed Graphify
   version. Do not rerun semantic extraction merely to discover code changes.
3. Verify that the sanitized semantic layer remains present and that the update contains only expected
   physical code/document changes.
4. Reject any `source_file` value that is neither a physical file nor a verbatim planned path in an
   authoritative context document.
5. Verify node and relationship counts, unique node IDs, and zero orphan relationships.
6. Query the completed feature plus at least one caller/dependency and compare the result with physical
   files and authoritative contracts.
7. Export a clean Obsidian vault only after every validation passes. Never export into a stale vault.
8. If any gate fails, retain the committed source, restore the previous graph/vault backup, and report
   the Graphify failure separately.

Automatic `$graphify . --update`, `/graphify . --update`, `graphify watch`, and Graphify Git hooks remain
disabled for this repository until a separately reviewed update script enforces the gates above.

## Completion gate

From F-001 onward, a feature is not `DONE` until all applicable commands pass:

```powershell
uv lock --check
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run pytest -q
uv run python -m compileall -q src
.\scripts\smoke-ui.ps1
```

`uv lock --check` and `uv sync --locked` must fail rather than silently modify a stale lockfile. The
smoke script must start the server on a bounded test port, poll Streamlit health, verify an HTTP success
response, and stop only the exact process it created. Record `NOT_RUN` with a reason for any unexecuted
command; never convert it to `PASS`.

Confirm that no secret, customer document, raw prompt/response, generated artifact, database, model
cache, runtime log, Graphify output, or Obsidian vault file entered tracked source.

## Git boundary

Agents may inspect `git status`, diff, log, and history. The human owns branches, staging, commits,
rebases, merges, pushes, tags, PRs, and releases unless a later prompt explicitly authorizes one named
action.

## Default build request

> Use the validated canonical Graphify graph in query-only mode, then read all six authoritative
> context files in the required order. Implement only the current `READY` feature in
> `coding-agent-context/project-overview.md`. Follow the architecture, layout, coding standard, and
> workflow rules; use Ponytail full plus its review; run the completion gate; append verified progress;
> perform no Git or Graphify mutation; and stop before the next feature.
