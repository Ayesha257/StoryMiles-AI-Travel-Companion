# Starts the backend API locally (after running setup_local.ps1 once).
# Run from the backend folder:  .\scripts\run_dev.ps1
$ErrorActionPreference = "Stop"
Push-Location "$PSScriptRoot\.."
try {
    & ".\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
} finally {
    Pop-Location
}
