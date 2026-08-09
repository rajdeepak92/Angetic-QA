# GraphRAG Agents — target architecture and stack

> This file defines the approved greenfield target. “Target” never means “already implemented.”

Related files: [product scope](./project-overview.md), [layout](./layout.md),
[AI workflow rules](./ai-workflow-rules.md), and [progress](./progress-tracker.md).

## Authority

| Question | Authority |
|---|---|
| What behavior must exist? | `project-overview.md` |
| Which technologies and runtime contracts apply? | `project-architecture-stack.md` |
| Where must code and tests live? | `layout.md` |
| How may an agent change the project? | `ai-workflow-rules.md` |
| What was actually changed and verified? | `progress-tracker.md` |
| Exact implemented behavior | Validated code, tests, schemas, migrations, and `uv.lock` |

Reconcile documentation conflicts before coding. Source code from an older repository is reference
material only when the human explicitly authorizes it.

## Runtime topology

`Browser -> Streamlit UI -> RunCoordinator -> LangGraph workflow -> services/agents -> ports ->
provider/persistence adapters -> PostgreSQL + Neo4j + Chroma + immutable artifacts`

- Streamlit is presentation and composition only; it contains no extraction, model, retrieval, or SQL logic.
- `RunCoordinator` accepts a typed request and yields sanitized `WorkflowEvent` values.
- LangGraph owns stage/node transitions, durable state, and checkpoint boundaries.
- Deterministic services own parsing, chunking, identities, canonicalization, coverage, and artifacts.
- Agents own only grounded structured model tasks.
- Ports isolate application logic from provider SDKs and stores; adapters implement the ports.

The MVP executes one workflow synchronously per browser session and streams node updates into UI
placeholders. Do not add ad-hoc background threads or call Streamlit APIs inside graph nodes. Durable
checkpoints make recovery possible if the browser/WebSocket session ends.

## Local server contract

| Setting | Required value |
|---|---|
| Framework | Streamlit `>=1.60,<2`; `uv.lock` pins the exact version |
| Bind address | `127.0.0.1` |
| Default port | `8501` |
| Entrypoint | `src/multi_agentic_graph_rag/ui/app.py` |
| Start command | `uv run streamlit run src/multi_agentic_graph_rag/ui/app.py` |
| Navigation | `st.Page` + `st.navigation(position="top")` |
| Chat | `st.chat_message` + bottom `st.chat_input` |
| Execution detail | `st.status` and `st.progress` |
| Workflow diagram | Native `st.mermaid_chart`; no custom JavaScript component |
| Modal credentials | One `st.dialog` containing a batched `st.form` |
| UI tests | `streamlit.testing.v1.AppTest` plus pytest |

`.streamlit/config.toml` fixes address/port/theme and preserves Streamlit’s default CORS/XSRF
protections. Binding to `0.0.0.0` is forbidden for this local MVP.

## UI composition

| Surface | Required contents |
|---|---|
| Global frame | Page config, top navigation, product identity, sanitized health indicator. |
| Workbench | Run header, Mermaid graph, execution status, artifacts/evidence, conversation, bottom composer. |
| Runs | Project/run filters, target stage, timestamps, state, resumability, sanitized error, artifact links. |
| Settings | Capability-specific provider/model selectors, Azure deployments, device/runtime fields, connection tests. |
| System Health | Dependency, provider, database, filesystem, and model-cache readiness without secret values. |

UI components consume immutable view models. They do not import provider SDKs, database drivers, or
workflow internals. Presenters map domain events/statuses to labels, colors, diagram text, and tables.

## State boundaries

| State | Owner | Rules |
|---|---|---|
| UI selection/history | Streamlit Session State | Presentation-only; may reset with the WebSocket session. |
| Ephemeral credentials | Session-scoped credential bundle | Strings only; never cached, serialized, logged, checkpointed, or written. |
| Workflow state | LangGraph + PostgreSQL checkpointer | JSON-serializable, no clients/secrets/raw document bodies. |
| Canonical product state | PostgreSQL | Project/run scoped and transactionally authoritative. |
| Retrieval projections | Neo4j and Chroma | Rebuildable from canonical records/manifests. |
| Generated files | Filesystem | Immutable, checksummed, project/run scoped. |

Do not put credentials or provider clients in `st.cache_data` or `st.cache_resource`. Shared cache
entries are cross-session; cached resources may be mutable singletons. Session loss requires the user
to re-enter missing UI credentials, while the durable run remains resumable.

## Approved technology

| Concern | Choice | Constraint |
|---|---|---|
| OS | Windows 11; PowerShell-first scripts | Probe prerequisites; do not assume Python, uv, Docker, or Node exists. |
| Language | Python `>=3.12,<3.13` | Fully type production code; no second application runtime. |
| Package/build | `uv`, `uv.lock`, Hatchling, `src/` layout | Lockfile is exact package-version authority. |
| UI | Streamlit 1.60+ | Native components first; thin presentation layer. |
| Workflow | LangGraph `StateGraph` with PostgreSQL checkpointer | Explicit state/events; synchronous durability for stage boundaries. |
| Contracts | Pydantic v2 | Strict models and `extra="forbid"` at trust boundaries. |
| Documents | PyMuPDF, `python-docx` | Preserve file/page/block/paragraph provenance. |
| IDs/checksums | `uuid-utils` UUIDv7 plus stdlib SHA-256/JSON | Never generated by a model. |
| PostgreSQL | `psycopg[binary,pool]` + LangGraph Postgres checkpoint adapter | Canonical records, runs, contexts, lineage, leases, checkpoints. |
| Knowledge graph | Neo4j official Python driver | Rebuildable projection only. |
| Vector index | ChromaDB | One normalized collection per project; fingerprint/dimension required. |
| Cloud models | `openai`/`tiktoken` and `google-genai` optional extras | Explicit provider adapters; no fallback. |
| Reranking | Hugging Face Hub, sentence-transformers, PyTorch optional extra | Local cross-encoder; explicit model revision/device. |
| Infrastructure | Docker Compose for PostgreSQL and Neo4j | Added in F-003; Chroma is embedded/local. |
| Observability | Python logging with redaction and run context | No raw secrets, prompts, responses, or customer documents. |
| Quality | pytest, Streamlit AppTest, Ruff, mypy strict | Tests ship with each feature. |

### F-003 implemented persistence baseline

| Concern | Implemented contract |
|---|---|
| Python clients | Lock-pinned `psycopg[binary,pool] 3.3.4`, `neo4j 6.2.0`, `chromadb 1.5.9`, and `uuid-utils 0.17.0`. |
| Containers | Official pinned `postgres:18.4-bookworm` and `neo4j:2026.06.0-community` images. |
| Project topology | Compose project `agentic-qa`; PostgreSQL `127.0.0.1:55432 -> 5432`; Neo4j `127.0.0.1:7474/7687`; isolated `backend` network. |
| Durable data | Compose volumes `postgres-data` and `neo4j-data`; embedded Chroma under ignored `runtime/databases/chroma`. |
| Canonical schema | PostgreSQL schema `agentic_qa` owns projects/runs and an immutable migration checksum ledger. |
| Projection bootstrap | F-003 established rebuildable project scope/checksum metadata; F-006 adds allowlisted project-scoped `Chunk` and embedding records with readback verification. |
| Credential source | Store passwords resolve from process environment; `start-infra.ps1` may load only the two store-password names from ignored local `.env`. Provider secrets are never read from it. |
| Reset | Normal Compose down preserves data; exact project confirmation plus label/path validation is required before volume and Chroma deletion. |

F-006 is complete: provider embedding adapters, project/run-scoped `Chunk` and Chroma embedding
projection methods, fingerprint/dimension readback checks, and the immutable
`requirements/chunk_manifest.json` service passed the strict completion gate.

Do not add Typer, FastAPI, Celery, Redis, React, LangChain wrappers, ORM, or a custom component unless
a later accepted feature proves that the existing stack cannot meet its contract.

## Initial model catalog

| Capability | Provider | Approved choices | Default |
|---|---|---|---|
| Reasoning | OpenAI | `gpt-5.6`, `gpt-5.6-terra`, `gpt-5.6-luna` | `gpt-5.6` |
| Embedding | OpenAI | `text-embedding-3-small`, `text-embedding-3-large` | `text-embedding-3-small` |
| Reasoning | Google Gemini | `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` | `gemini-2.5-flash` |
| Embedding | Google Gemini | `gemini-embedding-2` | `gemini-embedding-2` |
| Reasoning/embedding | Azure OpenAI | User-configured deployment aliases, capability checked | No invented default |
| Reranking | Hugging Face | `BAAI/bge-reranker-base`, `cross-encoder/ms-marco-MiniLM-L6-v2` | `BAAI/bge-reranker-base` |

Only stable provider models enter the default catalog. Updating a model/embedding revision is an
explicit architecture change. An embedding model, dimension, or revision change invalidates the
collection fingerprint and requires full re-embedding; vectors from incompatible spaces never mix.

OpenAI, Gemini, and Azure OpenAI are not presented as reranker providers. Azure’s dropdown displays
configured deployment aliases because API calls use the deployment name, which may differ from the
underlying model name.

## Credential and configuration contract

| Provider | Secret fields | Non-secret fields |
|---|---|---|
| OpenAI | API key | Model, reasoning settings |
| Google Gemini | API/auth key | Model, thinking settings |
| Azure OpenAI | API key | Endpoint, reasoning deployment, embedding deployment |
| Hugging Face | Token only for private/gated model | Model ID, revision, device, offline mode |

Credential resolution is `session dialog > OS environment > ignored local .env`. Non-secret setting
resolution is `session setting > OS environment > config.json`. The UI may persist only non-secret
settings after explicit confirmation. `.env.example` contains names/placeholders only.

The dialog groups missing fields by unique provider. Same-provider reasoning/embedding reuse one
provider credential; different providers remain isolated. “Test connection” returns only provider,
capability, selected model/deployment, latency, and sanitized success/error.

## Data ownership

| Store | Owns | Must not own |
|---|---|---|
| PostgreSQL | Sources, chunks, requirements, stories, scenarios, coverage, run/stage state, contexts, lineage, leases, checkpoints | Vector/graph search semantics. |
| Neo4j | `Chunk`, `Entity`, `MENTIONS`, and `USES`, `SUPPORTS`, `CONTROLS`, `COLLECTS_FROM`, `COMMUNICATES_VIA`, `CONNECTS_TO`, `REFERS_TO` | Canonical records or model-invented edge types. |
| Chroma | Chunk embeddings and retrieval metadata for one project collection | Canonical text/workflow state or cross-project results. |
| Filesystem | Immutable JSON artifacts and sanitized logs | Credentials or mutable canonical state. |

## Artifact contract

| Stage | Required project/run-relative artifacts |
|---|---|
| Stage 1.1 | `requirements/source_ledger.json`, `requirements/chunk_manifest.json` |
| Stage 1.2 | `requirements/requirements.json` |
| Stage 2 | `user-stories/story_context.json`, `user-stories/progress_story.json`, `user-stories/user-stories.json` |
| Stage 3 | `test-scenario/scenario_context.json`, `test-scenario/progress_scenario.json`, `test-scenario/test-scenarios.json`, `test-scenario/coverage.json` |

Every artifact has schema version, project/run identity, provenance, and checksum. Never edit an
artifact in place or treat an incompatible artifact as resumable.

## Development agent tooling

| Tool | Role | Project policy |
|---|---|---|
| [Graphify](https://github.com/Graphify-Labs/graphify) | Builds/query-updates a graph of tracked context, code, configuration, and call paths. | External development tool; `graphify-out/` remains ignored and local. Do not use `--code-only` because these five Markdown files are required context. |
| [Ponytail](https://github.com/DietrichGebert/ponytail) | Applies YAGNI/stdlib/native/reuse/minimum-code discipline and reviews over-engineering. | External agent plugin in `full` mode; it may not cut validation, security, recovery, accessibility, or accepted behavior. |

Graphify describes current repository relationships; it does not decide requirements. Ponytail
minimizes implementation; it does not remove accepted scope.
