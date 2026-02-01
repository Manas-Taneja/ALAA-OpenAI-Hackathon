param(
    [switch]$Reset
)

$ErrorActionPreference = "Stop"

$env:PYTHONPATH = "src"

if ($Reset) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupPath = "data\mistakes.$timestamp.jsonl"
    if (Test-Path "data\mistakes.jsonl") {
        Move-Item "data\mistakes.jsonl" $backupPath
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText("data\mistakes.jsonl", "", $utf8NoBom)
    Write-Host "Reset mistakes.jsonl (backup: $backupPath)"
}

Write-Host "=== Demo: before rule ==="
python -m anti_lazy run "api-answers: How does the orchestrator enforce retrieval?"

Write-Host "`n=== Add rule ==="
python -m anti_lazy feedback "api-answers" "*" "Always cite at least one snippet_id." --severity high

Write-Host "`n=== Demo: after rule ==="
python -m anti_lazy run "api-answers: How does the orchestrator enforce retrieval?"

Write-Host "`n=== Latest run log ==="
Get-Content data\runs.jsonl -Tail 1

if ($Reset) {
    if (Test-Path $backupPath) {
        Move-Item $backupPath "data\mistakes.jsonl" -Force
        Write-Host "Restored mistakes.jsonl from $backupPath"
    }
}
