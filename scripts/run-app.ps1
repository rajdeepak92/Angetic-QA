[CmdletBinding()]
param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8501
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

uv run streamlit run src/multi_agentic_graph_rag/ui/app.py `
    --server.address 127.0.0.1 `
    --server.port $Port
