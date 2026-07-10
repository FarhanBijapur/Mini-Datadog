$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $PSScriptRoot
$ContractPath = Join-Path $RootDir "contracts\openapi\mini-datadog.openapi.json"
$BaseUrl = if ($env:SPECMATIC_TEST_BASE_URL) { $env:SPECMATIC_TEST_BASE_URL } else { "http://127.0.0.1:8000" }

Push-Location $RootDir
try {
    python .\scripts\export_openapi.py
    specmatic test $ContractPath --testBaseURL=$BaseUrl
}
finally {
    Pop-Location
}
