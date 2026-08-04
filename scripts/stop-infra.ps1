[CmdletBinding()]
param(
    [switch]$RemoveVolumes,
    [string]$ConfirmProject = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectName = "agentic-qa"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$composePath = Join-Path $repositoryRoot "infra\compose.yaml"
$databaseRoot = [IO.Path]::GetFullPath((Join-Path $repositoryRoot "runtime\databases"))
$chromaPath = [IO.Path]::GetFullPath((Join-Path $databaseRoot "chroma"))

if ($RemoveVolumes -and $ConfirmProject -cne $projectName) {
    throw "Volume deletion requires -ConfirmProject '$projectName'."
}

$hadPostgresPassword = Test-Path Env:MAGR_POSTGRES_PASSWORD
$hadNeo4jPassword = Test-Path Env:MAGR_NEO4J_PASSWORD
$originalPostgresPassword = $env:MAGR_POSTGRES_PASSWORD
$originalNeo4jPassword = $env:MAGR_NEO4J_PASSWORD

try {
    if ([string]::IsNullOrWhiteSpace($env:MAGR_POSTGRES_PASSWORD)) {
        $env:MAGR_POSTGRES_PASSWORD = "compose-stop-placeholder"
    }
    if ([string]::IsNullOrWhiteSpace($env:MAGR_NEO4J_PASSWORD)) {
        $env:MAGR_NEO4J_PASSWORD = "compose-stop-placeholder"
    }

    $composeArguments = @("--project-name", $projectName, "--file", $composePath, "down")
    if ($RemoveVolumes) {
        $allowedVolumes = @(
            "${projectName}_neo4j-data",
            "${projectName}_postgres-data"
        )
        $projectVolumes = @(
            docker volume ls `
                --filter "label=com.docker.compose.project=$projectName" `
                --format "{{.Name}}"
        )
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to enumerate Agentic-QA project volumes."
        }
        foreach ($volume in $projectVolumes) {
            if ($volume -notin $allowedVolumes) {
                throw "Refusing reset: unexpected project volume '$volume'."
            }
            $label = docker volume inspect `
                --format "{{ index .Labels \"com.docker.compose.project\" }}" `
                $volume
            if ($LASTEXITCODE -ne 0) {
                throw "Unable to inspect project volume '$volume'."
            }
            if ($label -cne $projectName) {
                throw "Refusing reset: volume '$volume' failed project-label validation."
            }
        }
        $composeArguments += "--volumes"
    }

    docker compose @composeArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Agentic-QA Compose shutdown failed."
    }

    if ($RemoveVolumes -and (Test-Path -LiteralPath $chromaPath)) {
        if (-not $chromaPath.StartsWith("$databaseRoot\", [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing reset: Chroma path is outside the project database root."
        }
        Remove-Item -LiteralPath $chromaPath -Recurse -Force
        Write-Host "Removed project Chroma data at $chromaPath"
    }

    if ($RemoveVolumes) {
        Write-Host "Stopped Agentic-QA infrastructure and removed validated project data."
    }
    else {
        Write-Host "Stopped Agentic-QA infrastructure; persistent data was preserved."
    }
}
finally {
    if ($hadPostgresPassword) {
        $env:MAGR_POSTGRES_PASSWORD = $originalPostgresPassword
    }
    else {
        Remove-Item Env:MAGR_POSTGRES_PASSWORD -ErrorAction SilentlyContinue
    }
    if ($hadNeo4jPassword) {
        $env:MAGR_NEO4J_PASSWORD = $originalNeo4jPassword
    }
    else {
        Remove-Item Env:MAGR_NEO4J_PASSWORD -ErrorAction SilentlyContinue
    }
}
