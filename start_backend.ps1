$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$project = Join-Path $root "agrosense_backend"
$python = Join-Path $root "venv\Scripts\python.exe"

if (!(Test-Path $python)) {
  throw "Python not found at $python"
}

Set-Location $project
& $python manage.py runserver 127.0.0.1:8000 --noreload
