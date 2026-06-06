$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$python = Join-Path $root "venv\Scripts\python.exe"

if (!(Test-Path $python)) {
  throw "Python not found at $python"
}

Set-Location $root
& $python -m http.server 3000
