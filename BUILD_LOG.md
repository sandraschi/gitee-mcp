# gitee-mcp — Native (Tauri/NSIS) Build Log

## 2026-09-17T15:41+02:00 — First NSIS build after assfix (87/100, commit 7153da7)

Ran the fleet `nsis-build` protocol end to end. Repo layout note: this repo uses
`src-tauri/` (not `native/`) for the Tauri shell — all paths below are relative to
`src-tauri/`.

### Phase 1 — Pre-flight config audit (fixes applied)

| File | Issue found | Fix |
|---|---|---|
| `src-tauri/tauri.conf.json` | `security.csp` was a full CSP string, not `null` | Set to `null` |
| `src-tauri/tauri.conf.json` | `bundle.resources` only listed the backend `.exe`, no `.env.example` | Added `resources/.env.example` (copied from repo root `.env.example`); confirmed no real `.env` is present anywhere in the repo |
| `src-tauri/tauri.conf.json` | Attempted snake_case `install_mode`/`installer_hooks`/`create_desktop_shortcut` per the task brief's stated Tauri 2.11+ convention | **Reverted to camelCase** (`installMode`, `installerHooks`) after verifying against the installed CLI (`tauri-cli 2.11.4`) and its own schema (`https://schema.tauri.app/config/2`): the schema rejects snake_case for `NsisConfig`, uses camelCase, and has **no** `createDesktopShortcut` key at all. The task brief's claim that Tauri 2.11+ switched this to snake_case does not hold for this installed toolchain — flagging as a correction to the fleet doc/brief rather than silently following it into a broken build. |
| `src-tauri/resources/gitee-mcp-backend.exe` | Missing entirely (empty `resources/` dir) | Built via PyInstaller from `gitee-mcp-backend.spec` |
| `gitee-mcp-backend.spec` | PyInstaller couldn't resolve `fastmcp`'s own `importlib.metadata.version()` lookup at runtime → frozen exe crashed with `PackageNotFoundError: No package metadata was found for fastmcp-slim`/`fastmcp` | Added `copy_metadata("fastmcp")`, `copy_metadata("fastmcp-slim")`, `copy_metadata("mcp")` to `Analysis(datas=...)` (the existing strip/keep `.dist-info` filter alone wasn't sourcing the metadata in the first place) |
| `pyproject.toml` / `.venv` | `pyinstaller` was only available as a standalone `uv tool` (isolated env with no visibility into project deps: uvicorn, fastmcp, etc.) — first PyInstaller build silently produced a broken exe missing `uvicorn` entirely | `pyinstaller>=6.0.0` added as a proper project dependency; `.venv\Scripts\pyinstaller.exe` now used so the frozen build sees the real project environment |
| `src-tauri/src/backend.rs` | `free_port()` was single-layer (`taskkill` only, no poll-for-actually-free) | Rewrote as 4-layer: `Stop-Process` → `taskkill` → UAC-elevated `taskkill` → poll up to 240s (`port_is_free()`) |
| `src-tauri/src/backend.rs` | No independent TCP-connect health confirmation, only the `"Uvicorn running"` log-line match | Added `poll_backend_health()`, a TCP-connect loop (30× 2s) run on its own thread, emitting `backend-status: ready` independently of the stdout watcher |
| `src-tauri/src/backend.rs` | **Root cause of "Backend not reachable" on first CUA run**: `spawn_backend()` never passed `--mode http` to the backend exe, so it launched in its default `--mode stdio` (MCP stdio server) instead of the REST/uvicorn server Tauri expects on port 11161 | Added `.args(["--mode", "http", "--host", "127.0.0.1", "--port", "11161"])` to the spawned `Command` |
| `webapp/src/lib/use-zoom.ts` | `ZOOM_LEVELS` was `[0.8, 1.0, 1.25, 1.5, 2.0, 3.0]`, missing the mandated `0.5, 0.6, 0.7` steps; hook returned nothing (no indicator value) | Added missing levels, fixed `Ctrl+0` reset index, hook now returns `{ zoomPercent }` |
| `webapp/src/Layout.tsx` | No zoom % indicator in the UI; no "Restart Backend" button (only silent HTTP polling + Tauri event listener existed) | Added a `zoom: NN%` indicator and a "Restart Backend" button (shown when `backendOk === false`) that calls the existing `start_backend` Tauri command |
| `justfile` | No `build-native` or `cua-nsis-test` targets existed at all | Added both (see below) |
| `scripts/cua-smoke.py`, `scripts/cua-nsis-config.json` | Missing entirely — no CUA smoke harness had ever been instantiated for this repo | Copied the fleet-canonical template from `mcp-central-docs/templates/tauri-native/scripts/cua-smoke.py` (unmodified, v4) and wrote a gitee-mcp-specific `cua-nsis-config.json` (product name, port 11161, `/api/health` + `/api/v1/diagnostics` paths, `src-tauri/...` nsis glob, full 11-item nav route list matching `webapp/src/Layout.tsx`'s `NAV` array) |

All edits were backed up with timestamped `.bak` copies before mutation (5 files touched: `tauri.conf.json`, `backend.rs`, `use-zoom.ts`, `Layout.tsx`, `justfile`), per fleet batch-mutation safety rule; `.bak` files removed after the build was verified green.

### Phase 2 — Build

`just build-native` (PyInstaller backend → webapp `bun run build` → `npx @tauri-apps/cli build --bundles nsis`). Rust compiled clean in ~2m09s cold, no warnings requiring fixes.

### Phase 3 — Build gate

```
Gitee MCP_0.1.0_x64-setup.exe   30,519,184 bytes (30.5 MB)
```
PASS (>= 1 MB).

### Phase 4 — CUA smoke test

`just cua-nsis-test` → **11/11 phases passed**:

| # | Phase | Result |
|---|---|---|
| 1 | Kill stale processes | PASS |
| 2 | Install NSIS (silent) | PASS |
| 3 | Launch app, backend health | PASS (healthy on attempt 4) |
| 4 | Verify window | PASS (1942x1106) |
| 5 | Screenshot | PASS (175,727 bytes) |
| 6 | Feature route `/api/health` | PASS (HTTP 200) |
| 7 | Diagnostics `/api/v1/diagnostics` | PASS (12 tools registered, no errors) |
| 8 | WebView bridge (OCR) | PASS |
| 9 | Nav click-through (all 11 sidebar pages: Dashboard, Trending, Search, Ecosystem, Chat, Skills, Inbox, API Docs, Settings, Logs, Help) | PASS — every page |
| 10 | Analyze app logs | PASS (no errors) |
| 11 | Uninstall | PASS (exit code 0). Script logged `WARNING: App may still be registered`; manually re-verified afterward — `HKCU\...\Uninstall` has no Gitee entry and `%LOCALAPPDATA%\Gitee MCP` no longer exists. Treating as a script-side timing false-positive, not a real cleanup defect. |

### Installer

`D:\Dev\repos\gitee-mcp\src-tauri\target\release\bundle\nsis\Gitee MCP_0.1.0_x64-setup.exe` — 30.5 MB.

### Not done in this pass

- Did not commit these changes (not asked to).
- Did not add `pytz`, `jsonschema`, `joserfc`, `h11`, `beartype`, `websockets`, `cachetools` as real dependencies — grepped `src/` and confirmed none are actually imported; they're stale/generic entries in the PyInstaller spec's `hiddenimports` list carried over from a shared template and can be pruned in a follow-up if desired.
