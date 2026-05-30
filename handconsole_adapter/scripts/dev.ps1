$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Desktop = Join-Path $Root "apps\desktop"

Write-Host "AirInk HandConsole Adapter dev runner" -ForegroundColor Cyan
Write-Host "Working directory: $Desktop"

Push-Location $Desktop
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
        npm install
    }

    Write-Host "Starting Tauri dev..." -ForegroundColor Green
    npm run tauri dev
}
finally {
    Pop-Location
}
