import { defineConfig } from '@playwright/test';

/** Where the environment (`make up`) is reachable from this container (host network). */
export const WEB = process.env['E2E_WEB_URL'] ?? 'http://localhost:4200';
export const MAILPIT = process.env['E2E_MAILPIT_URL'] ?? 'http://localhost:8025';

export default defineConfig({
  testDir: './specs',
  // One story told in order (invite, activate, sign in): the tests share what the first creates.
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [['list']],
  use: {
    baseURL: WEB,
    // The application and Keycloak follow the browser's language: the texts asserted are Spanish.
    locale: 'es-CO',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [{ name: 'chromium', use: { browserName: 'chromium' } }],
});
