# Multi-Agent Clinical Information Extraction System Setup and Startup Script

$ErrorActionPreference = "Continue"

Clear-Host
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Starting Multi-Agent Clinical Decision Support System  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Clean up existing processes running on target ports (8080, 5173) to avoid socket binding errors
Write-Host "`nChecking for existing processes on ports 8080 and 5173..." -ForegroundColor Yellow
$ports = @(8080, 5173)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($connections) {
        $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($p in $pids) {
            if ($p -and $p -gt 0) {
                Write-Host "Killing process $p using port $port..." -ForegroundColor Cyan
                Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
            }
        }
    }
}
# Create logs directory and log files
$logDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$backendLog = Join-Path $logDir "backend.log"
$frontendLog = Join-Path $logDir "frontend.log"
"" | Out-File -FilePath $backendLog -Encoding utf8
"" | Out-File -FilePath $frontendLog -Encoding utf8

# Start API Service as a background job
Write-Host "`n[1/2] Spawning FastAPI Service (Backend on port 8080)..." -ForegroundColor Yellow
$job1 = Start-Job -Name "FastAPI" -ScriptBlock {
    Set-Location $using:PWD
    $env:PYTHONPATH='.'
    $env:PYTHONUNBUFFERED='1'
    .\venv\Scripts\uvicorn backend.api.routes:app --reload --host 127.0.0.1 --port 8080 2>&1
}

# Start React Frontend as a background job
Write-Host "`n[2/2] Spawning React Frontend (Vite)..." -ForegroundColor Yellow
$job2 = Start-Job -Name "Vite" -ScriptBlock {
    Set-Location "$using:PWD\frontend"
    npx vite --host 127.0.0.1 --port 5173 2>&1
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   Multi-Agent Clinical System startup commands triggered!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Access Endpoints:" -ForegroundColor Cyan
Write-Host " - Frontend Application : http://localhost:5173"
Write-Host " - FastAPI Swagger UI   : http://localhost:8080/docs"
Write-Host " - Log files saved to   : $logDir"
Write-Host "`nPress Ctrl+C to stop the servers. Streaming logs live below..." -ForegroundColor Yellow
Write-Host "==========================================================`n"

# TCP connect test — more reliable than Get-NetTCPConnection for child processes
function Test-TcpPort($port) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $conn = $tcp.BeginConnect("127.0.0.1", $port, $null, $null)
        $wait = $conn.AsyncWaitHandle.WaitOne(500, $false)  # 500ms timeout
        if ($wait -and $tcp.Connected) {
            $tcp.Close()
            return $true
        }
        $tcp.Close()
        return $false
    } catch {
        return $false
    }
}

# Job alive check — catches crashes that don't release the port
function Test-JobAlive($job) {
    return ($job.State -eq "Running")
}

# Helper to drain logs from background jobs, print to terminal, and append to log files
function Flush-JobLogs {
    $backendLogs = Receive-Job -Job $job1 -ErrorAction SilentlyContinue
    if ($backendLogs) {
        foreach ($line in $backendLogs) {
            Write-Host "[BACKEND] $line" -ForegroundColor Cyan
            $line | Out-File -FilePath $backendLog -Append -Encoding utf8
        }
    }

    $frontendLogs = Receive-Job -Job $job2 -ErrorAction SilentlyContinue
    if ($frontendLogs) {
        foreach ($line in $frontendLogs) {
            Write-Host "[FRONTEND] $line" -ForegroundColor Green
            $line | Out-File -FilePath $frontendLog -Append -Encoding utf8
        }
    }
}

# Active startup poll — wait up to 60s for both services to come alive while streaming logs
Write-Host "Waiting for servers to start..." -ForegroundColor DarkGray
$maxWait = 60
$elapsed = 0
while ($elapsed -lt $maxWait) {
    # Drain and output logs immediately during startup
    Flush-JobLogs

    $backendUp  = Test-TcpPort 8080
    $frontendUp = Test-TcpPort 5173

    if ($backendUp -and $frontendUp) {
        Write-Host "`n[OK] Both services are live (backend: $backendUp, frontend: $frontendUp)" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 1
    $elapsed += 1
}
if ($elapsed -ge $maxWait) {
    Write-Host "[WARN] Timeout waiting for services. Entering monitor anyway..." -ForegroundColor Yellow
}

try {
    $backendFails  = 0
    $frontendFails = 0
    $maxFails      = 5

    while ($true) {
        # Drain any buffered output from background jobs live to terminal & files
        Flush-JobLogs

        # Backend: TCP connect + job alive
        $backendPort = Test-TcpPort 8080
        $backendJob  = Test-JobAlive $job1
        if ($backendPort -or $backendJob) { $backendFails = 0 } else { $backendFails++ }

        # Frontend: TCP connect OR job alive
        $frontendJob  = Test-JobAlive $job2
        $frontendPort = Test-TcpPort 5173
        if ($frontendPort -or $frontendJob) { $frontendFails = 0 } else { $frontendFails++ }

        if ($backendFails -ge $maxFails) {
            Write-Host "`n[ERROR] FastAPI backend is down (port:$backendPort job:$backendJob for $($backendFails * 2)s)!" -ForegroundColor Red
            break
        }

        if ($frontendFails -ge $maxFails) {
            Write-Host "`n[ERROR] Vite frontend job has stopped for $($frontendFails * 2)s!" -ForegroundColor Red
            break
        }

        # Status line every 15s so terminal doesn't look frozen
        if (($elapsed % 15) -eq 0) {
            Write-Host "  [STATUS] backend:$backendPort($backendJob)  frontend:$frontendPort($frontendJob)" -ForegroundColor DarkGray
        }
        $elapsed += 2
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host "`nStopping background jobs..." -ForegroundColor Yellow
    Stop-Job  -Job $job1, $job2 -ErrorAction SilentlyContinue
    Remove-Job -Job $job1, $job2 -ErrorAction SilentlyContinue
}
