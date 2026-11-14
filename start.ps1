$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Najpierw zainstaluj zależności: uv sync --python 3.12' }
Push-Location frontend
try {
    if (-not (Test-Path 'node_modules')) {
        & npm.cmd ci
        if ($LASTEXITCODE -ne 0) { throw 'Instalacja frontendu nie powiodła się.' }
    }
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Build frontendu nie powiódł się.' }
} finally { Pop-Location }
$serverHealth = $null
try { $serverHealth = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 2 } catch { }
if ($serverHealth) {
    if (-not $serverHealth.pipeline) { throw 'Na porcie 8000 odpowiada inna usługa. Nie została zatrzymana.' }
    if (-not $serverHealth.source_sha256 -or $serverHealth.code_changed) {
        throw 'Na porcie 8000 działa wcześniejszy kod backendu. Zakończ jego pracę po ukończeniu zadań i ponów start.ps1. Sam build frontendu nie aktualizuje Pythona.'
    }
    Write-Host 'Aplikacja już działa: http://127.0.0.1:8000 (frontend przebudowany, kod backendu zgodny).'
    return
}
& .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
