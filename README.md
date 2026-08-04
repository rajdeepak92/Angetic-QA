# GraphRAG Agents

Windows-local Streamlit shell for the Multi-Agentic QA Knowledge GraphRAG product.

## Prerequisites

- Windows 11 and PowerShell
- Git
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop with Linux containers (required for PostgreSQL and Neo4j)

Node.js is used only by optional development-agent hooks.

If uv is missing, install it with the approved Windows package:

```powershell
winget install --id=astral-sh.uv -e
```

## Bootstrap

From the repository root:

```powershell
.\scripts\bootstrap.ps1
```

The script probes required and optional tools, installs Python 3.12 through uv, and synchronizes the
locked project environment.

## Run

```powershell
.\scripts\run-app.ps1
```

Open <http://127.0.0.1:8501>. The equivalent direct command is:

```powershell
uv run streamlit run src/multi_agentic_graph_rag/ui/app.py
```

## Configure providers

`config.json` contains only validated non-secret defaults. Optional OS environment overrides are
listed in `.env.example`; the application intentionally does not read a local `.env` file.

Open **Settings** to select approved reasoning, embedding, and reranking models. Applying settings
prompts once for each missing unique provider credential. Credentials are password inputs held only
in Streamlit Session State and can be cleared explicitly. **Test connections** performs bounded,
user-triggered provider checks and shows only sanitized status and latency.

Open **System Health** to inspect Python, Streamlit, local directory, reranker-cache, selected-provider,
last connection-check, PostgreSQL, Neo4j, and embedded Chroma readiness.

## Start persistence services

Set local database passwords in the current process, or place only the two `MAGR_*_PASSWORD` values
in the ignored root `.env`; provider credentials are never loaded from that file. Do not write real
values into tracked files:

```powershell
$env:MAGR_POSTGRES_PASSWORD = "<local-postgres-password>"
$env:MAGR_NEO4J_PASSWORD = "<local-neo4j-password-at-least-8-characters>"
.\scripts\start-infra.ps1
```

The project-scoped Compose stack starts PostgreSQL on `127.0.0.1:55432` and Neo4j on
`127.0.0.1:7474`/`127.0.0.1:7687`, waits for health, and applies PostgreSQL migrations
idempotently. Chroma persists locally under ignored `runtime/databases/chroma`.

Check sanitized store health:

```powershell
docker compose --project-name agentic-qa --file infra/compose.yaml ps
uv run python -c "from multi_agentic_graph_rag.bootstrap import build_app_context; print([port.check_health() for port in build_app_context().persistence_checks])"
```

Stop services without deleting data:

```powershell
.\scripts\stop-infra.ps1
```

The destructive local reset below removes only validated `agentic-qa` Compose volumes and the
project Chroma directory. It requires the exact project confirmation and cannot be undone:

```powershell
.\scripts\stop-infra.ps1 -RemoveVolumes -ConfirmProject agentic-qa
```

## Verify

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
