# gitee-mcp start script - naked-PC safe (winget installs uv + node + bun)
param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$NoBrowser
)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendPort = 11161
$FrontendPort = 11162

$Host.UI.RawUI.WindowTitle = "gitee-mcp - backend :$BackendPort / frontend :$FrontendPort"

if (-not $Headless) {
    Write-Host ""
    Write-Host "  gitee-mcp - Gitee bridge (Chinese GitHub)" -ForegroundColor Cyan
    Write-Host "  BACKEND   http://127.0.0.1:$BackendPort   (REST /api, MCP /mcp, Swagger /docs)" -ForegroundColor Gray
    Write-Host "  FRONTEND  http://127.0.0.1:$FrontendPort  (webapp UI)" -ForegroundColor Gray
    Write-Host ""
}

# --- Require-Command: winget auto-install for naked PCs ---------------------
function Require-Command {
    param([string]$Name, [string]$WingetId, [string]$Url)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Write-Host "  Installing $Name via winget..." -ForegroundColor Yellow
        winget install --id $WingetId -e --accept-source-agreements --accept-package-agreements
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
        if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
            throw "$Name still not found after winget install. Install manually: $Url"
        }
    }
}

Require-Command "uv" "astral-sh.uv" "https://astral.sh/uv/"
Require-Command "node" "OpenJS.NodeJS" "https://nodejs.org/"

# --- Clear port zombies -------------------------------------------------------
Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# --- Backend -------------------------------------------------------------------
Write-Host "-> backend (uv run uvicorn :$BackendPort)..." -ForegroundColor Yellow
$BackendJob = Start-Job -Name "gitee-backend" -ScriptBlock {
    param($Root, $Port)
    Set-Location $Root
    uv run uvicorn gitee_mcp.server:app --host 127.0.0.1 --port $Port --log-level info
} -ArgumentList $Root, $BackendPort

$ready = $false
for ($i = 0; $i -lt 90; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
    Start-Sleep -Seconds 1
}
if (-not $ready) {
    Receive-Job $BackendJob -Keep | Out-String | Write-Host
    throw "Backend did not become healthy on :$BackendPort within 90s. Check uv sync / .env"
}
Write-Host "  backend healthy" -ForegroundColor Green

if ($BackendOnly) {
    while ($true) {
        if ($BackendJob.State -in @("Completed", "Failed")) { Receive-Job $BackendJob; break }
        Start-Sleep -Seconds 2
    }
    exit
}

# --- Frontend -------------------------------------------------------------------
# Resolve bun to a real executable path. PS 5.1 Start-Process cannot launch a
# bare command name that resolves to a shim, and fresh shells often lack
# %USERPROFILE%\.bun\bin on PATH - so resolve once, use everywhere.
function Resolve-Bun {
    param([string]$RootDir)
    $candidates = @()
    $cmd = Get-Command bun.exe -ErrorAction SilentlyContinue
    if ($cmd) { $candidates += $cmd.Source }
    $cmd2 = Get-Command bun -ErrorAction SilentlyContinue
    if ($cmd2 -and $cmd2.CommandType -eq "Application") { $candidates += $cmd2.Source }
    $userBun = Join-Path $env:USERPROFILE ".bun\bin\bun.exe"
    if (Test-Path $userBun) { $candidates += $userBun }
    foreach ($c in $candidates) {
        if (Test-Path $c) { return $c }
    }
    Write-Host "  Installing Bun via winget..." -ForegroundColor Yellow
    winget install --id Oven-sh.Bun -e --accept-source-agreements --accept-package-agreements
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
    if (Test-Path $userBun) { return $userBun }
    throw "Bun not found after winget install. Expected at $userBun - install manually from https://bun.sh"
}

$WebRoot = Join-Path $Root "webapp"
$BunPath = Resolve-Bun $Root
if (-not (Test-Path (Join-Path $WebRoot "node_modules"))) {
    Write-Host "-> bun install (first run)..." -ForegroundColor Yellow
    & $BunPath install
}

Write-Host "-> frontend (vite :$FrontendPort)..." -ForegroundColor Yellow
Start-Process -NoNewWindow -FilePath $BunPath -ArgumentList "run", "dev", "--", "--port", "$FrontendPort", "--host", "127.0.0.1", "--strictPort" -WorkingDirectory $WebRoot

# --- Browser ---------------------------------------------------------------------
if (-not $NoBrowser -and -not $Headless) {
    $feReady = $false
    for ($i = 0; $i -lt 60; $i++) {
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:$FrontendPort" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($r.StatusCode -eq 200) { $feReady = $true; break }
        } catch { }
        Start-Sleep -Seconds 1
    }
    if ($feReady) {
        Write-Host "  opening webapp..." -ForegroundColor Green
        Start-Process "http://127.0.0.1:$FrontendPort"
    }
}

# --- Keep alive --------------------------------------------------------------------
while ($true) {
    if ($BackendJob.State -in @("Completed", "Failed")) {
        Write-Host "Backend exited - restarting..." -ForegroundColor Red
        Receive-Job $BackendJob | Out-String | Write-Host
        break
    }
    Start-Sleep -Seconds 2
}
