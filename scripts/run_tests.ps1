$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot

Set-Location $projectRoot

$env:AIRWRITE_ENV = "test"
$env:AIRWRITE_CONFIG_DIR = "tests/output/config"
$env:AIRWRITE_DATA_DIR = "tests/output/data"
$env:AIRWRITE_LOG_DIR = "tests/output/logs"

New-Item -ItemType Directory -Force -Path $env:AIRWRITE_CONFIG_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $env:AIRWRITE_DATA_DIR | Out-Null
New-Item -ItemType Directory -Force -Path $env:AIRWRITE_LOG_DIR | Out-Null

$testTargets = @(
    "tests/unit",
    "tests/integration",
    "tests/packaging"
) | Where-Object { Test-Path $_ }

& .\.venv\Scripts\python -m pytest $testTargets -v
