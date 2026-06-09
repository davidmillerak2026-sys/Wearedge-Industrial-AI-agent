$ErrorActionPreference = "Stop"

$blockRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-Path (Join-Path $blockRoot "..\..")
$packagePath = Join-Path $repoRoot "wfc-blocks\wearedge-agent-service.zip"

if (Test-Path -LiteralPath $packagePath) {
    Remove-Item -LiteralPath $packagePath -Force
}

Compress-Archive -Path (Join-Path $blockRoot "*") -DestinationPath $packagePath -Force
Write-Host "Created $packagePath"
