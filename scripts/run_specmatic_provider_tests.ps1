$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot

Push-Location $RootDir
try {
    python .\scripts\export_openapi.py
    specmatic test --config specmatic.yaml
}
finally {
    Pop-Location
}
