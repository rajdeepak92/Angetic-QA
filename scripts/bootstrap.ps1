[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$requiredCommands = @("git", "uv")
$optionalCommands = @("winget", "docker", "node")
$missingRequired = @()

foreach ($commandName in $requiredCommands + $optionalCommands) {
    $command = Get-Command $commandName -ErrorAction SilentlyContinue
    if ($null -eq $command) {
        Write-Host "${commandName}: NOT FOUND"
        if ($commandName -in $requiredCommands) {
            $missingRequired += $commandName
        }
    }
    else {
        Write-Host "${commandName}: $($command.Source)"
    }
}

if ($missingRequired.Count -gt 0) {
    if ("uv" -in $missingRequired) {
        Write-Host "Install uv with: winget install --id=astral-sh.uv -e"
    }
    throw "Missing required command(s): $($missingRequired -join ', ')"
}

uv python install 3.12
uv sync --frozen
