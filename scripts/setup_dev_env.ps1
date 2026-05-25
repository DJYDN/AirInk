$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot

Set-Location $projectRoot

python -m venv .venv
.\.venv\Scripts\python -m pip install --index-url https://pypi.org/simple --upgrade pip
.\.venv\Scripts\python -m pip install --index-url https://pypi.org/simple -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python -m pip freeze | Set-Content requirements.lock.txt
