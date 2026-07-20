# Creates the storymiles role/database using the postgres superuser password.
# Usage:
#   $env:PGPASSWORD = 'your-postgres-password'
#   .\scripts\bootstrap_db.ps1
$ErrorActionPreference = "Stop"

if (-not $env:PGPASSWORD) {
    throw "Set your postgres password first:  `$env:PGPASSWORD = 'your-password'"
}

$psql = "C:\Program Files\PostgreSQL\18\bin\psql.exe"
if (-not (Test-Path $psql)) {
    $found = Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\psql.exe" | Sort-Object FullName -Descending | Select-Object -First 1
    if (-not $found) { throw "psql.exe not found" }
    $psql = $found.FullName
}

Write-Host "Using $psql"
& $psql -U postgres -h 127.0.0.1 -d postgres -v ON_ERROR_STOP=0 -c "DO `$`$ BEGIN CREATE USER storymiles WITH PASSWORD 'storymiles'; EXCEPTION WHEN duplicate_object THEN NULL; END `$`$;"
$dbExists = "$(& $psql -U postgres -h 127.0.0.1 -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = 'storymiles'")".Trim()
if ($dbExists -ne "1") {
    & $psql -U postgres -h 127.0.0.1 -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE storymiles OWNER storymiles;"
}
& $psql -U postgres -h 127.0.0.1 -d storymiles -v ON_ERROR_STOP=1 -c "GRANT ALL ON SCHEMA public TO storymiles; ALTER SCHEMA public OWNER TO storymiles;"
Write-Host "Database ready."
