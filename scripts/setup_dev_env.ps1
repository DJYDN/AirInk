param(
    [switch]$RefreshLockfile
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptRoot
$lockfilePath = Join-Path $projectRoot "requirements.lock.txt"

Set-Location $projectRoot

python -m venv .venv
.\.venv\Scripts\python -m pip install --index-url https://pypi.org/simple --upgrade pip
.\.venv\Scripts\python -m pip install --index-url https://pypi.org/simple -r requirements.txt -r requirements-dev.txt
.\.venv\Scripts\python -m pip install --index-url https://pypi.org/simple -e .

if ($RefreshLockfile) {
    $newLockfile = .\.venv\Scripts\python -m pip freeze
    $existingLockfile = if (Test-Path $lockfilePath) {
        Get-Content $lockfilePath -Raw
    } else {
        ""
    }
    $renderedLockfile = ($newLockfile -join [Environment]::NewLine).TrimEnd()

    if ($renderedLockfile -ne $existingLockfile.TrimEnd()) {
        Set-Content -Path $lockfilePath -Value $renderedLockfile
    }
}
