param(
    [int]$BackendPort = 8001,
    [int]$PreviewPort = 4173
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RuntimeDir = Join-Path $ProjectRoot ".runtime"
$LogDir = Join-Path $RuntimeDir "logs"
$EnvFile = Join-Path $ProjectRoot ".env.local"
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

if (-not (Test-Path $EnvFile)) {
    & (Join-Path $PSScriptRoot "setup-local-mysql.ps1")
}

Get-Content -LiteralPath $EnvFile | ForEach-Object {
    if ($_ -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
        Set-Item -Path "Env:$($Matches[1])" -Value $Matches[2]
    }
}

if (-not (Get-NetTCPConnection -LocalPort 3307 -State Listen -ErrorAction SilentlyContinue)) {
    & (Join-Path $PSScriptRoot "setup-local-mysql.ps1")
}

$venvPython = Join-Path $BackendDir "venv\Scripts\python.exe"
$python = if (Test-Path $venvPython) { $venvPython } else { (Get-Command python).Source }
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
if (-not $npm) {
    $npm = (Get-Command npm).Source
}

$backendHealth = "http://127.0.0.1:$BackendPort/health"
$backendRunning = $false
try {
    $response = Invoke-WebRequest -Uri $backendHealth -UseBasicParsing -TimeoutSec 3
    $backendRunning = $response.StatusCode -eq 200
} catch {
    $backendRunning = $false
}

if (-not $backendRunning) {
    Write-Host "Starting FastAPI: 127.0.0.1:$BackendPort"
    $backendOut = Join-Path $LogDir "backend.out.log"
    $backendErr = Join-Path $LogDir "backend.err.log"
    Start-Process -FilePath $python `
        -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$BackendPort" `
        -WorkingDirectory $BackendDir `
        -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr `
        -WindowStyle Hidden | Out-Null

    $deadline = (Get-Date).AddSeconds(40)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 700
        try {
            $response = Invoke-WebRequest -Uri $backendHealth -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                $backendRunning = $true
                break
            }
        } catch {
        }
    }
    if (-not $backendRunning) {
        throw "FastAPI failed to start. See $backendErr"
    }
}

Write-Host "Seeding admin and sample data (idempotent)"
Push-Location $BackendDir
try {
    & $python -m app.seed
    if ($LASTEXITCODE -ne 0) {
        throw "Database seed failed."
    }
} finally {
    Pop-Location
}

Write-Host "Building frontend production assets"
Push-Location $FrontendDir
try {
    & $npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "Frontend build failed."
    }
} finally {
    Pop-Location
}

$previewUrl = "http://127.0.0.1:$PreviewPort/"
$previewRunning = $false
try {
    $response = Invoke-WebRequest -Uri $previewUrl -UseBasicParsing -TimeoutSec 3
    $previewRunning = $response.StatusCode -eq 200
} catch {
    $previewRunning = $false
}

if (-not $previewRunning) {
    Write-Host "Starting frontend preview: 127.0.0.1:$PreviewPort"
    $env:VITE_BACKEND_PROXY = "http://127.0.0.1:$BackendPort"
    $previewOut = Join-Path $LogDir "frontend.out.log"
    $previewErr = Join-Path $LogDir "frontend.err.log"
    Start-Process -FilePath $npm `
        -ArgumentList "run", "preview", "--", "--host", "127.0.0.1", "--port", "$PreviewPort" `
        -WorkingDirectory $FrontendDir `
        -RedirectStandardOutput $previewOut -RedirectStandardError $previewErr `
        -WindowStyle Hidden | Out-Null

    $deadline = (Get-Date).AddSeconds(40)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 700
        try {
            $response = Invoke-WebRequest -Uri $previewUrl -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                $previewRunning = $true
                break
            }
        } catch {
        }
    }
    if (-not $previewRunning) {
        throw "Frontend preview failed to start. See $previewErr"
    }
}

Write-Host "Local site is ready: $previewUrl"
Write-Host "API health: http://127.0.0.1:$PreviewPort/api/health"

