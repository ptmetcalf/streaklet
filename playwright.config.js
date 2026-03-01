const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  timeout: 60000,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:8092',
    trace: 'on-first-retry'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    }
  ],
  webServer: {
    command: 'bash -lc "source .venv/bin/activate && DB_PATH=/tmp/streaklet-playwright.db APP_SECRET_KEY=Fy-0rzbjp1FJw5KScrXmw0C52rd4e4s_DDQ9IJ00YdI= uvicorn app.main:app --host 127.0.0.1 --port 8092"',
    url: 'http://127.0.0.1:8092/profiles',
    timeout: 120000,
    reuseExistingServer: true
  }
});
