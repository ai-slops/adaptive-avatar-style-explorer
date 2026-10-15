import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "tests",
  fullyParallel: false,
  use: {
    baseURL: "http://127.0.0.1:8766",
    headless: true,
    viewport: { width: 1440, height: 1000 },
    launchOptions: { args: ["--no-sandbox"] },
  },
  webServer: [
    {
      command: "../../.venv/bin/python tests/run_server.py",
      url: "http://127.0.0.1:8766/",
      reuseExistingServer: false,
      timeout: 30000,
    },
    {
      command: "../../.venv/bin/python tests/run_codex_server.py",
      url: "http://127.0.0.1:8767/",
      reuseExistingServer: false,
      timeout: 30000,
    },
  ],
  reporter: "list",
});
