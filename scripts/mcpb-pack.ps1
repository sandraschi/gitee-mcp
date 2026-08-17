# Fresh-stage MCPB pack: wipe+recopy src -> mcpb/src, verify 3-4-100, then pack.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Pkg = "gitee_mcp"
$Stage = Join-Path $Root "mcpb\src\$Pkg"

Write-Host "=== gitee-mcp MCPB pack ===" -ForegroundColor Cyan

# 1. Fresh stage: wipe + recopy (never pack a stale twin)
if (Test-Path (Join-Path $Root "mcpb\src")) {
    Remove-Item -Recurse -Force (Join-Path $Root "mcpb\src")
    Write-Host "  wiped stale mcpb/src" -ForegroundColor Yellow
}
New-Item -ItemType Directory -Force -Path (Split-Path $Stage) | Out-Null
Copy-Item -Recurse -Force (Join-Path $Root "src\$Pkg") $Stage
Write-Host "  staged src/$Pkg -> mcpb/src/$Pkg" -ForegroundColor Green

# 2. Copy manifest + README + CHANGELOG if present
Copy-Item (Join-Path $Root "manifest.json") (Join-Path $Root "mcpb\manifest.json") -Force
Copy-Item (Join-Path $Root "assets") (Join-Path $Root "mcpb\assets") -Recurse -Force
if (Test-Path (Join-Path $Root "README.md")) { Copy-Item (Join-Path $Root "README.md") (Join-Path $Root "mcpb\README.md") -Force }
if (Test-Path (Join-Path $Root "CHANGELOG.md")) { Copy-Item (Join-Path $Root "CHANGELOG.md") (Join-Path $Root "mcpb\CHANGELOG.md") -Force }

# 3. Verify no pollution under mcpb/
$polluted = Get-ChildItem (Join-Path $Root "mcpb") -Recurse -Include "*.pyc", "__pycache__", "*.bak", "*.bak.*" -ErrorAction SilentlyContinue
if ($polluted) {
    throw "mcpb/ contains pollution: $($polluted.FullName -join ', ') - aborting"
}
Write-Host "  mcpb/ pollution check clean" -ForegroundColor Green

# 4. 3-4-100 verification (HARD gate)
function Word-Count([string]$Path) {
    if (-not (Test-Path $Path)) { return 0 }
    (@(Get-Content -Raw $Path) -split '\s+' | Where-Object { $_ }).Count
}
$sys = Word-Count (Join-Path $Root "assets\prompts\system.md")
$user = Word-Count (Join-Path $Root "assets\prompts\user.md")
$ex = (Get-Content (Join-Path $Root "assets\prompts\examples.json") -Raw | ConvertFrom-Json).Count
Write-Host "  prompts: system=$sys words, user=$user words, examples=$ex entries" -ForegroundColor Gray
if ($sys -lt 3000 -or $user -lt 4000 -or $ex -lt 100) {
    throw "3-4-100 FAIL: system=$sys user=$user examples=$ex (need 3000 / 4000 / 100)"
}
Write-Host "  3-4-100 gate PASSED" -ForegroundColor Green

# 5. Verify entry point imports from mcpb/src only
$env:PYTHONPATH = Join-Path $Root "mcpb\src"
$check = uv run python -c "import sys; sys.path.insert(0, r'$Stage\..'); import gitee_mcp.server; print('import OK')" 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "mcpb entry import failed: $check"
}
Write-Host "  entry import OK" -ForegroundColor Green

# 6. Pack
Push-Location (Join-Path $Root "mcpb")
New-Item -ItemType Directory -Force -Path (Join-Path $Root "dist") | Out-Null
bunx @anthropic-ai/mcpb pack . (Join-Path $Root "dist\gitee-mcp-v0.1.0.mcpb")
if ($LASTEXITCODE -ne 0) { throw "mcpb pack failed" }
Pop-Location

# 7. Optional cleanup of staging
Remove-Item -Recurse -Force (Join-Path $Root "mcpb\src") -ErrorAction SilentlyContinue
Write-Host "=== MCPB pack complete ===" -ForegroundColor Green
