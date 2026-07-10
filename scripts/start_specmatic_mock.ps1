$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$ContractPath = Join-Path $RootDir "contracts\openapi\mini-datadog.openapi.json"
$Port = if ($env:SPECMATIC_MOCK_PORT) { $env:SPECMATIC_MOCK_PORT } else { "9000" }

Push-Location $RootDir
try {
    python .\scripts\export_openapi.py
    specmatic mock $ContractPath --port $Port
}
finally {
    Pop-Location
}
