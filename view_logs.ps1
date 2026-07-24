# Helper Script to Tail Live System & Agent Logs
param(
    [ValidateSet("backend", "frontend", "app")]
    [string]$Service = "backend"
)

$logFile = Join-Path $PSScriptRoot "logs\$Service.log"

if (-not (Test-Path $logFile)) {
    Write-Host "[!] Log file $logFile does not exist yet. Run .\run_all.ps1 first to generate logs." -ForegroundColor Red
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Tailing live $Service logs ($logFile) " -ForegroundColor Cyan
Write-Host " Press Ctrl+C to exit log viewer" -ForegroundColor Yellow
Write-Host "==========================================================`n" -ForegroundColor Cyan

Get-Content -Path $logFile -Wait -Tail 40
