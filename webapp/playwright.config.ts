import { defineConfig } from "@playwright/test";

const BACKEND_PORT = 11161;
const FRONTEND_PORT = 11162;

export default defineConfig({
  testDir: "./e2e",
  timeout: 60000,
  retries: 1,
  use: {
    baseURL: `http://127.0.0.1:${FRONTEND_PORT}`,
    headless: true,
    screenshot: "only-on-failure",
  },
  webServer: {
    command: `uv run uvicorn gitee_mcp.server:app --host 127.0.0.1 --port ${BACKEND_PORT} --log-level warning`,
    port: BACKEND_PORT,
    cwd: "../",
    timeout: 60000,
    reuseExistingServer: false,
    env: {
      // small seed set: the full 25-seed radar exceeds the anonymous hourly quota
      GITEE_SEED_REPOS: "dromara/hutool,macrozheng/mall",
    },
  },
});
