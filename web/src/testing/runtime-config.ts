import { type Provider } from '@angular/core';

import { RUNTIME_CONFIG, type RuntimeConfig } from '@core/config/runtime-config';

/** A complete config for tests; override only what the test is about. */
export const TEST_RUNTIME_CONFIG: RuntimeConfig = {
  apiUrl: 'http://api.test',
  keycloak: { url: 'http://auth.test', realmPrefix: 'agilina-', clientId: 'agilina-web' },
  logLevel: 'debug',
};

export function provideTestRuntimeConfig(overrides: Partial<RuntimeConfig> = {}): Provider {
  return { provide: RUNTIME_CONFIG, useValue: { ...TEST_RUNTIME_CONFIG, ...overrides } };
}
