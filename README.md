# GraphRAG Agents

Windows-local Streamlit shell for the Multi-Agentic QA Knowledge GraphRAG product.

## Prerequisites

- Windows 11 and PowerShell
- Git
- [uv](https://docs.astral.sh/uv/)

Docker Desktop is not required until F-003. Node.js is used only by optional development-agent hooks.

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
and last connection-check readiness. PostgreSQL, Neo4j, and Chroma checks begin with F-003.

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
