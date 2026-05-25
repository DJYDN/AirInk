$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$testsOutputRoot = Join-Path $projectRoot "tests/output"
$configDir = Join-Path $testsOutputRoot "config"
$dataDir = Join-Path $testsOutputRoot "data"
$logDir = Join-Path $testsOutputRoot "logs"

Set-Location $projectRoot

$env:AIRWRITE_ENV = "test"
$env:AIRWRITE_CONFIG_DIR = $configDir
$env:AIRWRITE_DATA_DIR = $dataDir
$env:AIRWRITE_LOG_DIR = $logDir

New-Item -ItemType Directory -Force -Path $env:AIRWRITE_CONFIG_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $env:AIRWRITE_DATA_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $env:AIRWRITE_LOG_DIR | Out-Null

$testTargets = @(
    "tests/unit",
    "tests/integration",
    "tests/packaging"
) | Where-Object { Test-Path $_ }

& .\.venv\Scripts\python -m pytest $testTargets -v
