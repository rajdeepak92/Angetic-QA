[CmdletBinding()]
param(
    [ValidateRange(30, 300)]
    [int]$TimeoutSeconds = 180
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectName = "agentic-qa"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$composePath = Join-Path $repositoryRoot "infra\compose.yaml"
$envPath = Join-Path $repositoryRoot ".env"

foreach ($commandName in @("docker", "uv")) {
    if ($null -eq (Get-Command $commandName -ErrorAction SilentlyContinue)) {
        throw "Missing required command: $commandName"
    }
}

if (Test-Path -LiteralPath $envPath) {
    $localSecrets = Get-Content -LiteralPath $envPath -Raw | ConvertFrom-StringData
    foreach ($secretName in @("MAGR_POSTGRES_PASSWORD", "MAGR_NEO4J_PASSWORD")) {
        if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($secretName)) -and
            $localSecrets.ContainsKey($secretName)) {
            Set-Item -Path "Env:$secretName" -Value $localSecrets[$secretName]
        }
    }
}

if ([string]::IsNullOrWhiteSpace($env:MAGR_POSTGRES_PASSWORD)) {
    throw "Set MAGR_POSTGRES_PASSWORD in the current session."
}
if ([string]::IsNullOrWhiteSpace($env:MAGR_NEO4J_PASSWORD) -or $env:MAGR_NEO4J_PASSWORD.Length -lt 8) {
    throw "Set MAGR_NEO4J_PASSWORD to at least 8 characters in the current session."
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is unavailable."
}
docker compose --project-name $projectName --file $composePath config --quiet
if ($LASTEXITCODE -ne 0) {
    throw "Agentic-QA Compose configuration is invalid."
}
docker compose --project-name $projectName --file $composePath up `
    --detach `
    --wait `
    --wait-timeout $TimeoutSeconds
if ($LASTEXITCODE -ne 0) {
    throw "Agentic-QA services did not become healthy within $TimeoutSeconds seconds."
}

Push-Location $repositoryRoot
try {
    uv run python -c "from multi_agentic_graph_rag.bootstrap import build_app_context; build_app_context().run_repository.initialize_schema()"
    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL schema initialization failed."
    }
}
finally {
    Pop-Location
}

Write-Host "Agentic-QA infrastructure is healthy and PostgreSQL schema is current."
