[CmdletBinding()]
param(
    [ValidateRange(1, 65535)]
    [int]$Port = 8502,

    [ValidateRange(1, 300)]
    [int]$TimeoutSeconds = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pythonPath = (uv run python -c "import sys; print(sys.executable)").Trim()
$process = Start-Process `
    -FilePath $pythonPath `
    -ArgumentList @(
        "-m", "streamlit", "run", "src/multi_agentic_graph_rag/ui/app.py",
        "--server.address", "127.0.0.1",
        "--server.port", "$Port",
        "--server.headless", "true"
    ) `
    -PassThru `
    -WindowStyle Hidden

$deadline = [DateTimeOffset]::UtcNow.AddSeconds($TimeoutSeconds)
$healthUri = "http://127.0.0.1:$Port/_stcore/health"

try {
    while ([DateTimeOffset]::UtcNow -lt $deadline) {
        if ($process.HasExited) {
            throw "Streamlit exited before becoming healthy (exit code $($process.ExitCode))."
        }

        try {
            $response = Invoke-WebRequest -Uri $healthUri -TimeoutSec 2 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "Streamlit health check passed at $healthUri"
                exit 0
            }
        }
        catch [System.Net.WebException] {
            # The server is still starting; bounded polling continues until the deadline.
        }
        catch [System.Net.Http.HttpRequestException] {
            # PowerShell 7 wraps a refused startup connection with HttpClient exceptions.
        }
        catch [System.Threading.Tasks.TaskCanceledException] {
            # A single request timed out while the bounded startup poll remains active.
        }

        Start-Sleep -Milliseconds 250
    }

    throw "Streamlit did not become healthy within $TimeoutSeconds seconds."
}
finally {
    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id
        $process.WaitForExit()
    }
}
