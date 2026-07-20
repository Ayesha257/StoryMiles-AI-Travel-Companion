# One-time local setup for the StoryMiles backend without Docker.
# Prerequisites: Python 3.13 and PostgreSQL 17 installed.
# Run from the backend folder:  .\scripts\setup_local.ps1
$ErrorActionPreference = "Stop"

# Locate psql (PostgreSQL client)
$psql = Get-Command psql -ErrorAction SilentlyContinue
if (-not $psql) {
    $candidates = Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\psql.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending
    if ($candidates) { $psql = $candidates[0].FullName } else { throw "psql not found. Install PostgreSQL first (https://www.postgresql.org/download/windows/)." }
} else { $psql = $psql.Source }
Write-Host "Using psql: $psql"

# Create the app role + database (idempotent-ish: errors about existing objects are fine)
Write-Host "Creating 'storymiles' role and database (you will be asked for the postgres superuser password you chose during install)..."
& $psql -U postgres -h localhost -v ON_ERROR_STOP=0 -f "$PSScriptRoot\create_db.sql"

# Locate Python 3.13+
$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    $python = $python.Source
} elseif (Test-Path "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe") {
    $python = "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe"
} else {
    throw "Python 3.13 not found. Install it from https://www.python.org/downloads/ and check 'Add python.exe to PATH'."
}
Write-Host "Using Python: $python"

# Python virtual environment + dependencies
if (-not (Test-Path "$PSScriptRoot\..\.venv")) {
    Write-Host "Creating virtual environment..."
    & $python -m venv "$PSScriptRoot\..\.venv"
}
& "$PSScriptRoot\..\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$PSScriptRoot\..\.venv\Scripts\python.exe" -m pip install -r "$PSScriptRoot\..\requirements.txt"

# Database migrations + demo seed data
Push-Location "$PSScriptRoot\.."
try {
    & ".\.venv\Scripts\python.exe" -m alembic upgrade head
    & ".\.venv\Scripts\python.exe" -m app.seed
    Write-Host ""
    Write-Host "Setup complete. Start the API with:  .\scripts\run_dev.ps1"
} finally {
    Pop-Location
}
