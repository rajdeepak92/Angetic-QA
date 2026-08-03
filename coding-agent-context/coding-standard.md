# GraphRAG Agents — enterprise Python coding standard

> This file defines how humans and coding agents write, review, and verify production code. `MUST`,
> `MUST NOT`, `SHOULD`, and `MAY` are normative. Exceptions require an explicit feature contract,
> localized justification, and tests.

Related files: [product scope](./project-overview.md), [architecture](./project-architecture-stack.md),
[layout](./layout.md), [AI workflow rules](./ai-workflow-rules.md), and
[progress](./progress-tracker.md).

## Authority and scope

- Apply this standard to `src/`, tests, scripts, migrations, prompts, and configuration.
- Product behavior comes from `project-overview.md`; this file never authorizes new behavior.
- Technology and dependency choices come from `project-architecture-stack.md`.
- Package ownership and import direction come from `layout.md`.
- If an existing pattern conflicts with these contracts, fix the shared root or record a blocker; do
  not reproduce the conflict.
- The checked-in `pyproject.toml`, schemas, migrations, and tests enforce the exact implemented rules.

## Quality baseline

| Concern | Required standard |
|---|---|
| Python | `>=3.12,<3.13`; use modern syntax and `from __future__ import annotations`. |
| Encoding | UTF-8, LF in source files, four-space indentation, newline at end of file. |
| Format | Ruff formatter; line length `100`; no manual formatting exceptions. |
| Lint | Ruff with import sorting, correctness, modernization, bug-risk, logging, pytest, pathlib, and project rules. |
| Types | Mypy strict for all production code; tests remain typed where fixtures/fakes expose contracts. |
| Validation | Pydantic v2 strict models with `extra="forbid"` at every trust boundary. |
| Tests | Pytest with strict configuration/markers; Streamlit UI uses `AppTest`. |
| Documentation | PEP 257-compatible docstrings for public modules, classes, functions, and non-obvious contracts. |

Configure tools once in `pyproject.toml`. Do not scatter tool settings, broad exclusions, or warning
suppression across files. A localized suppression names the exact rule, states why it is safe, and has
a test when behavior could regress.

Initial enforcement baseline:

```toml
[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = [
  "E4", "E7", "E9", "F", "I", "UP", "B", "SIM", "C4", "C90", "DTZ", "G",
  "LOG", "PIE", "PT", "PTH", "RUF",
]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true
show_error_codes = true

[tool.pytest.ini_options]
addopts = "-ra --strict-config --strict-markers"
testpaths = ["tests"]
```

Add or suppress a rule only for a demonstrated project need. Ruff lint and formatter settings must remain
compatible; do not enable formatter-conflicting style rules.

## Design before code

1. Identify the active `F-###`, owning layer/file, inputs, outputs, trust boundaries, failure modes,
   persistence effects, UI evidence, and completion test.
2. Trace callers and implementations before modifying a shared contract.
3. Keep business decisions in deterministic services; keep I/O behind ports/adapters.
4. Prefer a pure core with an imperative shell: calculate first, then perform explicit side effects.
5. Make the smallest complete root-cause change. Do not scaffold future features or add speculative
   extension points.

Every module has one stable responsibility and one owning layer. Dependencies point inward toward
`domain` and `ports`. No import cycle, service locator, hidden registry, or module-global client is allowed.

## Naming and source organization

- Modules, functions, variables, and parameters use `snake_case`; classes and protocols use `CapWords`;
  constants use `UPPER_SNAKE_CASE`.
- Names express domain intent: `RequirementRepository`, `ReasoningModelPort`, `StageStarted`, and
  `ProviderTransientError`; avoid `Manager`, `Processor`, `Handler`, or `Data` without a precise qualifier.
- Boolean names start with `is_`, `has_`, `can_`, or `should_`. Units appear in names such as
  `timeout_seconds`, `duration_ms`, and `size_bytes`.
- Commands use imperative names; events use past-tense names; exceptions end in `Error`.
- Private implementation symbols start with `_`. Do not use wildcard imports or mutate `__all__` dynamically.
- Imports are absolute and grouped as standard library, third party, then project. Importing a module
  MUST NOT open a connection, read configuration, start a thread, mutate Streamlit state, or write a file.

Use one canonical definition for each schema, enum, status, identifier, and provider capability. Do not
duplicate constants across the UI, workflow, service, and adapter layers.

## Types and contracts

- Annotate every production function parameter and return value, including `None` returns.
- Use built-in generics (`list[str]`, `dict[str, int]`) and `X | None`; avoid legacy typing aliases.
- Use `Protocol` in `ports/` for substitutable capabilities. Accept the narrowest protocol and return
  domain values, not vendor SDK objects.
- Use enums or constrained values for provider, stage, status, artifact kind, and error category; no
  stringly typed control flow.
- Stable structured data uses Pydantic models, frozen dataclasses, or explicit `TypedDict` graph state;
  do not pass anonymous dictionaries across layers.
- `Any` is forbidden in project-owned contracts. At an untyped SDK boundary, isolate it in the adapter
  and validate/narrow it before returning.
- A `# type: ignore[code]` is last resort, must name the exact mypy code and reason, and must not hide a
  project-owned typing defect. Do not use global `ignore_missing_imports`.
- Avoid `cast()` as validation. Cast only after a runtime check or a library guarantee documented beside it.

Canonical boundary model:

```python
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from multi_agentic_graph_rag.domain.enums import TargetStage
from multi_agentic_graph_rag.domain.identifiers import ProjectId
from multi_agentic_graph_rag.domain.schemas.sources import SourcePath


class WorkflowRequest(BaseModel):
    """Validated request accepted by the workflow boundary."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        frozen=True,
        validate_default=True,
    )

    project_id: ProjectId
    source: SourcePath
    target_stage: TargetStage
```

Validation rejects unexpected or ambiguous input. Do not silently coerce identifiers, booleans, enums,
paths, provider names, model names, or model output into a valid-looking value.

## Functions and classes

- A function performs one cohesive operation at one abstraction level and has an explicit result.
- Keep cyclomatic complexity at or below `10`. Split decisions by domain responsibility, not arbitrary lines.
- Prefer early validation/returns over deeply nested branches. Replace boolean mode flags with typed commands
  or separate functions when behavior differs materially.
- Do not use mutable default arguments. Do not mutate caller-owned collections or LangGraph input state.
- Use keyword-only parameters for multiple same-typed or easily confused arguments.
- Inject clocks, identifier factories, model ports, repositories, and event sinks. Never read them from globals.
- Use context managers for files, transactions, cursors, locks, and clients that own resources.
- Prefer composition over inheritance. A base class requires a real invariant shared by multiple accepted
  implementations; otherwise use a protocol plus small concrete classes.
- Properties are side-effect free and inexpensive. Network, database, model, or filesystem work uses an
  explicit verb method.

## Determinism and time

- Model calls never create IDs, checksums, canonical ordering, timestamps, provenance, coverage, or success state.
- Create UUIDv7 values once through the identifier service and persist/reuse them across retries and resumes.
- Hash canonical UTF-8 bytes with SHA-256. Canonical JSON uses stable field/order rules and never `default=str`.
- Use timezone-aware UTC timestamps for persisted events. Inject a clock; do not call wall time throughout domain code.
- Use monotonic time for durations. Sort unordered inputs before their order affects identity, prompts, storage,
  artifacts, or tests.
- Random behavior requires an injected generator and seed in tests. Production correctness cannot depend on luck.

## Errors, transactions, and retries

- Define classified domain/application errors in `domain/errors.py`; translate vendor exceptions once at the adapter.
- Error categories distinguish validation, conflict, not-found, transient provider/store, permanent provider/store,
  integrity, and cancellation failures.
- Never use `assert` for runtime validation, catch-and-ignore, bare `except`, or `None`/empty collections as hidden failure.
- Catch only errors the current layer can recover from, enrich safely, or translate. Preserve the cause with
  `raise ... from error`.
- Log an exception once at the handling boundary; do not log-and-rethrow it through every layer.
- A transaction owns one explicit consistency unit. Commit only after all canonical invariants pass; rollback on error.
- Retry only allowlisted transient failures, with bounded attempts, timeout, exponential backoff/jitter, and an
  idempotency key. Validation, authentication, authorization, schema, and integrity failures are not retried.
- Never switch provider/model/store as fallback. Surface the selected dependency’s sanitized failure.

## Streamlit code

- Pages and components render typed view models and call typed application facades only.
- A page exports one `render(...)` function. Repeated presentation belongs in `ui/components/`; domain-to-view
  conversion belongs in `ui/presenters/`.
- Define stable, namespaced widget keys centrally in `ui/state/session.py`; do not create ad-hoc keys across pages.
- Treat every rerun as normal. Forms batch related settings; callbacks remain small and deterministic.
- Do not call models, SQL, Cypher, Chroma, or document parsers from a page/component.
- Never cache credentials, provider clients containing credentials, mutable workflow state, or project/run data
  without an explicit isolation-safe cache key and contract.
- UI errors are sanitized and actionable. Status, diagram, artifact, and conversation views reflect persisted or
  emitted state; the UI never manufactures a successful state.
- Use native Streamlit elements and accessible labels. Do not rely only on color or inject arbitrary HTML/JavaScript.

## LangGraph workflows and agents

- Graph state is a versioned `TypedDict` or strict model containing only minimal JSON-serializable references/state.
- Nodes accept state plus injected dependencies and return explicit partial updates; they do not mutate input state.
- Reducers are explicit for every concurrently updated field. Route decisions are deterministic Python functions.
- Node names and checkpoint meanings are stable once runs can persist. A schema change includes compatibility or an
  explicit non-resumable migration decision.
- Any external call/write before a checkpoint is idempotent because an interrupted node may execute again.
- Emit a sanitized `WorkflowEvent` for node start, progress, success, retry, and failure.
- Keep one grounded model responsibility per agent. Prompts live in versioned prompt files beside their owner.
- Supply bounded, source-scoped context; request native structured output; validate it strictly before domain use.
- No regex extraction of JSON from prose, invented evidence, silent repair, or empty-success fallback.
- Provider selection, credentials, retry policy, token limits, and timeouts remain outside prompts and model decisions.

## Persistence, queries, and artifacts

- PostgreSQL repositories require explicit `project_id` and `run_id` where applicable; no unscoped read/update/delete.
- Use parameterized SQL and Cypher values. Dynamic labels, relationship types, sort fields, or collection names come
  only from an allowlist; never interpolate user/model text.
- Keep transactions short and make uniqueness, foreign keys, checks, and concurrency invariants enforceable in schema.
- Avoid N+1 access patterns. Use bounded batches and measure before adding caches or denormalization.
- PostgreSQL commits canonical state first. Neo4j and Chroma writes are idempotent projections with fingerprint,
  parity, and readback checks; do not fake a distributed transaction.
- Chroma collection/filter operations always include the normalized project boundary and embedding fingerprint.
- Applied migrations are immutable. Add a new ordered migration with forward behavior, verification, and an explicit
  destructive/reset path when rollback cannot preserve data.
- Artifacts are schema-versioned, canonical, checksummed, immutable, and project/run scoped. Write through staging,
  verify, then finalize; never partially overwrite a published artifact.

## Security and privacy

- Treat UI input, paths, documents, environment values, database rows, model output, and provider responses as untrusted.
- Validate type, format, length, range, capability, and allowlisted values at the first trusted boundary.
- Resolve and enforce document-root containment, regular-file status, extension, size, and symlink policy before reading.
- Never use `eval`, `exec`, unsafe deserialization, dynamic imports, or shell execution of user/model content.
- Use `SecretStr` or a dedicated credential bundle at boundaries. Secrets never enter reprs, logs, exceptions, prompts,
  checkpoints, caches, artifacts, telemetry, test snapshots, or source control.
- Parameterize queries and use least-privilege store/provider credentials. Destructive actions require explicit,
  separately rendered confirmation and exact scope.
- Return sanitized messages to the UI and keep detailed non-secret diagnostics in local logs.
- Test redaction with representative key/token/connection-string patterns; do not test with live secrets.

## Logging and observability

- Each module uses `logger = logging.getLogger(__name__)`; library modules never call `basicConfig()`.
- Log structured lifecycle events with `event`, `project_id`, `run_id`, `stage`, `attempt`, duration, and counts when known.
- `DEBUG`: non-sensitive diagnostic decisions; `INFO`: stage/run lifecycle; `WARNING`: handled degradation/retry;
  `ERROR`: failed operation; `logger.exception`: one terminal boundary requiring a stack trace.
- Use deferred logging arguments rather than preformatted f-strings. Never log full documents, evidence text, prompts,
  model responses, embeddings, credentials, or raw exception payloads that may contain them.
- Redaction occurs before handler emission and cannot be disabled by normal UI settings.
- Metrics/status are derived from real events and monotonic durations; they do not alter workflow decisions.

## Performance and resource use

- Establish a measured bottleneck before optimizing. Correctness, evidence fidelity, and isolation remain mandatory.
- Bound document size, chunk count/size, retrieval candidates, reranker batch, context tokens, model output, query rows,
  retries, timeouts, and concurrency through validated configuration.
- Stream or batch large inputs instead of creating repeated full-document copies. Release files/cursors/clients promptly.
- Cache only pure or explicitly isolation-safe results with complete keys and invalidation rules. Never cache secrets.
- No ad-hoc threads, processes, or asyncio in the synchronous MVP. Add concurrency only through an accepted feature
  with ordering, cancellation, resource, Streamlit-session, and checkpoint tests.

## Testing standard

- Mirror source ownership under `tests/`; test through public behavior and ports, not private implementation steps.
- Name tests `test_<unit>_<condition>_<outcome>` and use Arrange–Act–Assert with one behavioral reason to fail.
- Every feature tests the happy path, invalid/ambiguous input, boundary values, dependency failure, redaction, project/run
  isolation, and any retry/idempotency behavior it introduces.
- Unit tests use deterministic fakes and inject clock, ID factory, filesystem root, clients, and event sink.
- Default tests make no live network/model call and require no API key, customer document, Docker service, or GPU.
- Reuse adapter contract tests across implementations. Parametrize provider/model combinations and capability failures.
- Streamlit `AppTest` verifies navigation, widget state, dialogs, commands, status transitions, errors, and artifact views.
- Integration tests use explicit markers and isolated test stores. A skip is visible and never counted as verified behavior.
- End-to-end tests use sanitized fixtures and provider fakes by default; live-provider tests are separate, opt-in diagnostics.
- Do not use arbitrary sleeps. Use injected clocks, deterministic events, or bounded polling with a clear timeout.
- A defect fix begins with a failing regression test at the lowest owning layer.

Coverage percentage is diagnostic, not proof. Completion requires direct assertions for every accepted contract and
failure gate changed by the feature.

## Dependencies, configuration, and compatibility

- Reuse the standard library or approved stack before adding a package. A new dependency requires active-feature need,
  maintained upstream, Python 3.12/Windows support, acceptable license/security posture, and tests at its adapter boundary.
- Add dependencies with uv so `pyproject.toml` and `uv.lock` change together. Provider/GPU packages remain optional extras.
- No compatibility shim, deprecated alias, dual code path, or fallback without an explicit supported-version contract.
- Configuration is strict, documented, has safe defaults, and fails fast on invalid combinations. Keep secrets separate.
- Environment-specific values never become import-time constants if tests or sessions must override them.

## Documentation and comments

- A docstring explains contract, invariants, units, side effects, and raised domain errors—not line-by-line implementation.
- Use a one-line imperative summary; add `Args`, `Returns`, and `Raises` only when annotations/names are insufficient.
- Comments explain why a non-obvious decision is safe or necessary. Delete stale narration and commented-out code.
- `TODO`/`FIXME` requires `TODO(F-###): reason and completion condition`; otherwise create no debt marker.
- Public README/workflow, context authorities, examples, schemas, and progress change in the same feature as behavior.

## Review and completion checklist

Before marking a change complete, answer every applicable item with evidence:

- [ ] Implements only the requested feature and preserves dependency direction.
- [ ] Uses the existing owner/root boundary; no duplicate contract or speculative abstraction.
- [ ] Fully typed; strict Pydantic validation at new/changed trust boundaries.
- [ ] Deterministic identities/provenance/order and idempotent replay behavior are preserved.
- [ ] Errors are classified, sanitized, and never converted into success or fallback.
- [ ] Secrets, customer content, and cross-project data cannot enter logs/cache/state/artifacts incorrectly.
- [ ] SQL/Cypher/path/model inputs are scoped, parameterized, and allowlisted where required.
- [ ] UI remains presentation-only and reflects truthful workflow events/state.
- [ ] Tests cover success, validation, failure, isolation, retry/idempotency, and regression behavior.
- [ ] Ruff format/check, mypy strict, pytest, compile, and Streamlit smoke gate pass.
- [ ] Documentation/progress and Graphify are synchronized; Ponytail review findings are resolved.

## Reference baseline

- [PEP 8 — Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 257 — Docstring Conventions](https://peps.python.org/pep-0257/)
- [Python typing documentation](https://docs.python.org/3/library/typing.html)
- [Pydantic strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/) and
  [`ConfigDict`](https://docs.pydantic.dev/latest/api/config/)
- [Ruff formatter](https://docs.astral.sh/ruff/formatter/) and
  [configuration](https://docs.astral.sh/ruff/configuration/)
- [Mypy strict mode](https://mypy.readthedocs.io/en/stable/command_line.html#cmdoption-mypy-strict)
- [Pytest good practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
- [Streamlit architecture](https://docs.streamlit.io/develop/concepts/architecture/architecture),
  [caching](https://docs.streamlit.io/develop/concepts/architecture/caching), and
  [AppTest](https://docs.streamlit.io/develop/api-reference/app-testing)
- [LangGraph graph API and idempotency](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [OWASP input validation](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html),
  [secrets management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html), and
  [logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
