$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$backendScript = Join-Path $root "start_backend.ps1"

if (!(Test-Path $backendScript)) {
  throw "Backend script not found: $backendScript"
}

Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $backendScript | Out-Null

Set-Location $root
.\start_frontend.ps1
