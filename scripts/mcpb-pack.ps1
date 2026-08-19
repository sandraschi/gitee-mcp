# Fresh-stage MCPB pack: wipe+recopy src -> mcpb/src, verify 3-4-100, then pack.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Pkg = "gitee_mcp"
$McpbDir = Join-Path $Root "mcpb"
$Stage = Join-Path $McpbDir "src\$Pkg"

# bun/bunx live in the user profile; PS 5.1 PATH may not include them after login.
$env:PATH = "$env:USERPROFILE\.bun\bin;$env:PATH"

Write-Host "=== gitee-mcp MCPB pack ===" -ForegroundColor Cyan

# 1. Fresh stage: wipe the WHOLE mcpb/ dir first (never pack a stale twin; the
#    mcpb CLI packs the cwd tree, so stale manifest/assets/pycache from prior
#    runs would be bundled). Then rebuild it from scratch.
if (Test-Path $McpbDir) {
    Remove-Item -Recurse -Force $McpbDir
    Write-Host "  wiped stale mcpb/" -ForegroundColor Yellow
}
New-Item -ItemType Directory -Force -Path (Split-Path $Stage) | Out-Null

# robocopy excludes __pycache__ / *.pyc (tests and smoke runs leave bytecode in src/);
# a raw Copy-Item would stage it and trip the pollution check below.
robocopy (Join-Path $Root "src\$Pkg") $Stage /E /XD __pycache__ /XF "*.pyc" /NFL /NDL /NJH /NJS /NC /NS | Out-Null
if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed to stage src/$Pkg (exit code $LASTEXITCODE)"
}
Write-Host "  staged src/$Pkg -> mcpb/src/$Pkg (pycache excluded)" -ForegroundColor Green

# 2. Copy manifest + README + CHANGELOG + assets + .mcpbignore.
#    .mcpbignore MUST be present in the mcpb/ cwd so the pack CLI applies the
#    same exclusions (venv/node_modules/webapp/tests/glama.json/...) - without it
#    the archive is packed with zero ignored files.
Copy-Item (Join-Path $Root "manifest.json") (Join-Path $McpbDir "manifest.json") -Force
Copy-Item (Join-Path $Root "assets") (Join-Path $McpbDir "assets") -Recurse -Force
Copy-Item (Join-Path $Root ".mcpbignore") (Join-Path $McpbDir ".mcpbignore") -Force
if (Test-Path (Join-Path $Root "README.md")) { Copy-Item (Join-Path $Root "README.md") (Join-Path $McpbDir "README.md") -Force }
if (Test-Path (Join-Path $Root "CHANGELOG.md")) { Copy-Item (Join-Path $Root "CHANGELOG.md") (Join-Path $McpbDir "CHANGELOG.md") -Force }

# 3. Verify no pollution under mcpb/
$polluted = Get-ChildItem $McpbDir -Recurse -Include "*.pyc", "__pycache__", "*.bak", "*.bak.*" -ErrorAction SilentlyContinue
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

# 5. Verify entry point imports from mcpb/src only.
#    PYTHONDONTWRITEBYTECODE prevents the import check from dropping .pyc files
#    into mcpb/src AFTER the pollution check (which would ship in the bundle).
$env:PYTHONPATH = Join-Path $McpbDir "src"
$env:PYTHONDONTWRITEBYTECODE = "1"
$check = uv run python -c "import sys; sys.path.insert(0, r'$Stage\..'); import gitee_mcp.server; print('import OK')" 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "mcpb entry import failed: $check"
}
Write-Host "  entry import OK" -ForegroundColor Green

# 6. Pack
Push-Location $McpbDir
New-Item -ItemType Directory -Force -Path (Join-Path $Root "dist") | Out-Null
bunx @anthropic-ai/mcpb pack . (Join-Path $Root "dist\gitee-mcp-v0.1.0.mcpb")
if ($LASTEXITCODE -ne 0) { throw "mcpb pack failed" }
Pop-Location

# 7. Optional cleanup of staging
Remove-Item -Recurse -Force $McpbDir -ErrorAction SilentlyContinue
Write-Host "=== MCPB pack complete ===" -ForegroundColor Green
