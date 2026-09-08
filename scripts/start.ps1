$ErrorActionPreference = 'Stop'

Set-Location (Split-Path -Parent $PSScriptRoot)

docker compose up -d postgres
$env:DATABASE_URL = 'postgresql://kabadiwala:kabadiwala_demo_password@localhost:5432/kabadiwala_connect'

Write-Host 'PostGIS is running on localhost:5432'
Write-Host 'Kabadiwala Connect is starting on http://127.0.0.1:8000'
Write-Host 'Dashboard: http://127.0.0.1:8000/dashboard/'

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
