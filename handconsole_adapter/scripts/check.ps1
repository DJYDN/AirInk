$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
$Desktop = Join-Path $Root "apps\desktop"

Write-Host "AirInk HandConsole Adapter check" -ForegroundColor Cyan
Write-Host "Working directory: $Desktop"

Push-Location $Desktop
try {
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
        npm install
    }

    Write-Host "Running frontend build..." -ForegroundColor Green
    npm run build

    Write-Host "Running Rust check..." -ForegroundColor Green
    Push-Location "src-tauri"
    try {
        cargo check
    }
    finally {
        Pop-Location
    }
}
finally {
    Pop-Location
}
