$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$distRoot = Join-Path $projectRoot "dist"
$specPath = Join-Path $projectRoot "AirWrite.spec"

Set-Location $projectRoot

& .\.venv\Scripts\python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --name AirWrite `
    --paths src `
    --specpath $projectRoot `
    --distpath $distRoot `
    --workpath (Join-Path $projectRoot "build") `
    --collect-all PySide6 `
    --hidden-import airwrite.main `
    src/airwrite/main.py

if (Test-Path $specPath) {
    Write-Host "PyInstaller spec written to $specPath"
}
