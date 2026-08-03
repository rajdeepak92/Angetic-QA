# GraphRAG Agents — enterprise project layout

> This file is the authoritative placement and dependency map. Create only paths required by the
> active feature; the complete tree is the destination, not permission to scaffold unused modules.

Related files: [product scope](./project-overview.md), [architecture](./project-architecture-stack.md),
[AI workflow rules](./ai-workflow-rules.md), and [progress](./progress-tracker.md).

## Target repository tree

```text
GraphRAG-Agents/
├── .streamlit/
│   └── config.toml                       # tracked non-secret local server/theme configuration
├── coding-agent-context/
│   ├── project-overview.md               # desired behavior and feature register
│   ├── progress-tracker.md               # append-only verified history
│   ├── project-architecture-stack.md     # approved technology/runtime contracts
│   ├── ai-workflow-rules.md              # coding-agent execution rules
│   └── layout.md                         # this placement/dependency contract
├── documents/
│   └── inbox/
│       └── .gitkeep                      # customer files are ignored
├── generated/
│   └── .gitkeep                          # project/run artifacts are ignored
├── runtime/
│   ├── databases/chroma/.gitkeep
│   ├── locks/.gitkeep
│   ├── logs/.gitkeep
│   └── staging/.gitkeep
├── infra/
│   └── compose.yaml                      # PostgreSQL and Neo4j only
├── scripts/
│   ├── bootstrap.ps1                     # prerequisite checks and uv/Python project bootstrap
│   ├── start-infra.ps1                   # exact Docker Compose startup/health checks
│   ├── stop-infra.ps1                    # non-destructive service stop
│   ├── run-app.ps1                       # local Streamlit startup
│   └── smoke-ui.ps1                      # bounded start/health/stop test
├── src/
│   └── multi_agentic_graph_rag/
│       ├── __init__.py
│       ├── bootstrap.py                  # sole composition root; wires ports to adapters
│       ├── config/
│       │   ├── __init__.py
│       │   ├── loader.py                 # precedence and non-secret config loading
│       │   ├── model_catalog.py          # capability/provider/model registry
│       │   └── settings.py               # strict Pydantic settings
│       ├── domain/
│       │   ├── __init__.py
│       │   ├── enums.py                  # stable domain/status enums
│       │   ├── errors.py                 # classified domain/application errors
│       │   ├── identifiers.py            # UUIDv7/checksum/canonical identity functions
│       │   └── schemas/
│       │       ├── __init__.py
│       │       ├── artifacts.py
│       │       ├── commands.py
│       │       ├── requirements.py
│       │       ├── runs.py
│       │       ├── scenarios.py
│       │       ├── sources.py
│       │       └── stories.py
│       ├── ports/
│       │   ├── __init__.py
│       │   ├── documents.py              # document reader protocol
│       │   ├── events.py                 # workflow event sink protocol
│       │   ├── models.py                 # reasoning/embedding/reranker protocols
│       │   └── repositories.py           # canonical/projection/checkpoint protocols
│       ├── adapters/
│       │   ├── __init__.py
│       │   ├── documents/
│       │   │   ├── __init__.py
│       │   │   ├── docx_reader.py
│       │   │   └── pdf_reader.py
│       │   ├── models/
│       │   │   ├── __init__.py
│       │   │   ├── azure_openai.py
│       │   │   ├── factory.py
│       │   │   ├── gemini.py
│       │   │   ├── huggingface_reranker.py
│       │   │   ├── json_output.py
│       │   │   └── openai.py
│       │   └── persistence/
│       │       ├── __init__.py
│       │       ├── chroma.py
│       │       ├── neo4j.py
│       │       ├── postgres.py
│       │       └── migrations/
│       │           ├── 0001_initial.sql
│       │           └── README.md
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── requirement_discovery.py
│       │   ├── test_scenario.py
│       │   ├── user_story.py
│       │   └── prompts/
│       │       ├── requirement_discovery.md
│       │       ├── test_scenario.md
│       │       └── user_story.md
│       ├── services/
│       │   ├── __init__.py
│       │   ├── artifact_writer.py
│       │   ├── canonicalization.py
│       │   ├── chunking.py
│       │   ├── command_parser.py
│       │   ├── coverage.py
│       │   ├── manifest.py
│       │   ├── parsing.py
│       │   ├── path_policy.py
│       │   ├── retrieval.py
│       │   ├── run_coordinator.py
│       │   └── source_ledger.py
│       ├── workflows/
│       │   ├── __init__.py
│       │   ├── events.py
│       │   ├── ingestion.py
│       │   ├── pipeline.py
│       │   ├── requirement_discovery.py
│       │   ├── state.py
│       │   ├── test_scenarios.py
│       │   └── user_stories.py
│       ├── observability/
│       │   ├── __init__.py
│       │   ├── logging.py
│       │   └── redaction.py
│       └── ui/
│           ├── __init__.py
│           ├── app.py                    # Streamlit entrypoint and shared frame only
│           ├── navigation.py             # st.Page/st.navigation declarations
│           ├── pages/
│           │   ├── __init__.py
│           │   ├── health.py
│           │   ├── runs.py
│           │   ├── settings.py
│           │   └── workbench.py
│           ├── components/
│           │   ├── __init__.py
│           │   ├── artifact_panel.py
│           │   ├── chat_panel.py
│           │   ├── credential_dialog.py
│           │   ├── execution_status.py
│           │   ├── provider_selectors.py
│           │   └── workflow_diagram.py
│           ├── presenters/
│           │   ├── __init__.py
│           │   └── workflow_presenter.py
│           └── state/
│               ├── __init__.py
│               ├── credentials.py
│               └── session.py
├── tests/
│   ├── unit/
│   │   ├── agents/
│   │   ├── domain/
│   │   ├── services/
│   │   ├── ui/
│   │   └── workflows/
│   ├── contract/
│   │   ├── models/
│   │   └── persistence/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
├── .env.example
├── .gitignore
├── config.json                           # tracked non-secret defaults
├── pyproject.toml
├── README.md
├── uv.lock
└── workflow.md
```

## Dependency direction

| Package | May import | Must not import |
|---|---|---|
| `domain` | Python stdlib, Pydantic | Any other project layer, Streamlit, SDK, driver. |
| `ports` | `domain`, typing/ABC | Adapters, UI, concrete SDKs/drivers. |
| `services` | `domain`, `ports`, narrow config values | Streamlit, concrete adapters, global state. |
| `agents` | `domain`, `ports`, prompt resources | UI, persistence adapters, direct filesystem writes. |
| `workflows` | `domain`, `ports`, `services`, `agents` | Streamlit components or concrete provider/database classes. |
| `adapters` | `domain`, `ports`, `config`, external SDKs | UI or workflow presentation. |
| `observability` | `domain` and stdlib logging | Business decisions or secret-bearing payload capture. |
| `ui` | Typed facades/view models from `domain`, `services`, `workflows` | Direct SQL/Cypher/Chroma/provider SDK calls. |
| `bootstrap.py` | All layers | Business logic; it only constructs and wires objects. |

Dependencies point inward toward domain/ports. Cross-layer cycles are forbidden. Use constructor
injection; do not hide clients, repositories, settings, or credentials in module globals.

## Directory ownership rules

- `config/`: validated settings and provider capability catalog, never secrets or business logic.
- `domain/`: canonical vocabulary, schemas, IDs, and error types independent of infrastructure.
- `ports/`: protocols/interfaces named by capability, not technology.
- `adapters/`: all vendor SDK, file-format, database, and network implementation details.
- `agents/`: one grounded model responsibility per file; prompts live beside the owning agent.
- `services/`: deterministic use-case logic; functions/classes must be testable without Streamlit or live services.
- `workflows/`: LangGraph state, nodes, edges, routing, checkpoint/event integration only.
- `observability/`: logging setup/redaction; never a second source of workflow state.
- `ui/`: rendering, navigation, session-only presentation state, dialogs, and presenters only.
- `tests/`: mirrors the owning source package and proves both success and failure contracts.

## UI placement rules

- `ui/app.py` sets page config, builds shared dependencies through `bootstrap.py`, declares navigation,
  and runs the selected page. It contains no feature implementation.
- Every page exports one `render(...)` entry and delegates repeated visuals to `components/`.
- Components accept typed values/callbacks and return typed user choices. They never open stores or call models.
- `presenters/` convert domain events to Mermaid, tables, badges, and sanitized display strings.
- `state/session.py` initializes named Session State keys; no page creates ad-hoc keys.
- `state/credentials.py` owns the ephemeral credential bundle and explicit clearing. It never persists.
- No custom HTML/JavaScript component or global CSS injection until native Streamlit is proven insufficient.

## File creation rules

1. Search Graphify and the tree for an existing owner.
2. Extend the owning file when responsibility is unchanged.
3. Create a file only for a new stable responsibility required by the active feature.
4. Add its mirrored test in the same change.
5. Update this file when the new path or dependency direction is architectural.

Do not create `utils.py`, `helpers.py`, `common.py`, `misc.py`, duplicate `schemas.py` files, or generic
base classes. Name files after a domain capability. Keep `__init__.py` free of side effects and broad
re-exports.

## Test placement

| Test type | Location | External dependencies |
|---|---|---|
| Unit | `tests/unit/<owner>/test_<module>.py` | None; use fakes through ports. |
| UI | `tests/unit/ui/` | Streamlit `AppTest` and injected fakes; no live API keys. |
| Contract | `tests/contract/` | One adapter contract reused against fakes/test instances. |
| Integration | `tests/integration/` | Explicit Docker/provider marker; skipped only with recorded reason. |
| End-to-end | `tests/e2e/` | Sanitized fixture and deterministic provider fakes by default. |

Test fixtures contain no customer data, live credentials, copied model responses, or mutable generated
artifacts. A regression test accompanies every defect fix.

## Repository hygiene

- Track the five `coding-agent-context/*.md` files, `.streamlit/config.toml`, `config.json`, and `.env.example`.
- Ignore `.env`, `.streamlit/secrets.toml`, `documents/inbox/**`, `generated/**`, `runtime/**`,
  `graphify-out/`, caches, logs, local databases, and model caches.
- Keep `.gitkeep` files only where an empty runtime directory is required.
- Never commit provider credentials, customer documents, runtime artifacts, database volumes, or raw traces.
