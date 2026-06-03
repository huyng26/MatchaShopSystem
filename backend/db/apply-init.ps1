param(
    [Parameter(Mandatory = $true)]
    [string]$DatabaseUrl,

    [switch]$UseDocker
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$initDir = Join-Path $scriptRoot "init"
$sqlFiles = Get-ChildItem -LiteralPath $initDir -Filter "*.sql" |
    Sort-Object Name

if (-not $sqlFiles) {
    throw "No SQL files found in $initDir"
}

foreach ($file in $sqlFiles) {
    Write-Host "Applying $($file.Name)..."

    if ($UseDocker) {
        docker run --rm `
            -v "${initDir}:/sql:ro" `
            postgres:16-alpine `
            psql $DatabaseUrl `
            -v "ON_ERROR_STOP=1" `
            -f "/sql/$($file.Name)"

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to apply $($file.Name). Check the database URL, username, password, host, and permissions."
        }
    }
    else {
        psql $DatabaseUrl `
            -v "ON_ERROR_STOP=1" `
            -f $file.FullName

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to apply $($file.Name). Check the database URL, username, password, host, and permissions."
        }
    }
}

Write-Host "Database init SQL applied successfully."
