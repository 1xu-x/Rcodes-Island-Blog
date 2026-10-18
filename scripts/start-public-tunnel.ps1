param(
    [int]$PreviewPort = 4173
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ToolsDir = Join-Path $ProjectRoot "tools"
$RuntimeDir = Join-Path $ProjectRoot ".runtime"
$LogDir = Join-Path $RuntimeDir "logs"
$Cloudflared = Join-Path $ToolsDir "cloudflared.exe"
$PidFile = Join-Path $RuntimeDir "cloudflared.pid"
$UrlFile = Join-Path $RuntimeDir "public-url.txt"

New-Item -ItemType Directory -Force -Path $ToolsDir, $LogDir | Out-Null

if (-not (Test-Path $Cloudflared)) {
    Write-Host "Downloading cloudflared (free quick tunnel client)"
    Invoke-WebRequest `
        -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" `
        -OutFile $Cloudflared
}

if (Test-Path $PidFile) {
    $oldPid = [int](Get-Content -LiteralPath $PidFile -Raw)
    $oldProcess = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
    if ($oldProcess) {
        Stop-Process -Id $oldPid -Force
    }
    Remove-Item -LiteralPath $PidFile -ErrorAction SilentlyContinue
}

$stdout = Join-Path $LogDir "cloudflared.out.log"
$stderr = Join-Path $LogDir "cloudflared.err.log"
Remove-Item -LiteralPath $stdout, $stderr, $UrlFile -ErrorAction SilentlyContinue

$process = Start-Process -FilePath $Cloudflared `
    -ArgumentList "tunnel", "--url", "http://127.0.0.1:$PreviewPort", "--no-autoupdate" `
    -RedirectStandardOutput $stdout -RedirectStandardError $stderr `
    -WindowStyle Hidden -PassThru
$process.Id | Set-Content -LiteralPath $PidFile

$publicUrl = $null
$deadline = (Get-Date).AddSeconds(50)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Milliseconds 900
    foreach ($log in @($stdout, $stderr)) {
        if (Test-Path $log) {
            $match = Select-String -LiteralPath $log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -AllMatches |
                Select-Object -First 1
            if ($match) {
                $publicUrl = $match.Matches[0].Value
                break
            }
        }
    }
    if ($publicUrl) {
        break
    }
}

if (-not $publicUrl) {
    throw "Could not obtain a public tunnel URL. See $stderr"
}

$publicUrl | Set-Content -LiteralPath $UrlFile -Encoding ascii
Write-Host "Public URL: $publicUrl"

