import { parseRuntimeConfig, RuntimeConfigError } from './runtime-config';

describe('parseRuntimeConfig', () => {
  const valid = {
    apiUrl: 'http://localhost:8000/',
    keycloak: { url: 'http://localhost:8080', realm: 'agilina', clientId: 'agilina-web' },
    logLevel: 'INFO',
  };

  it('accepts a complete config and normalizes it', () => {
    const config = parseRuntimeConfig(valid);

    expect(config.apiUrl).toBe('http://localhost:8000');
    expect(config.keycloak.realm).toBe('agilina');
    expect(config.logLevel).toBe('info');
  });

  it('maps the WARNING level of the environment to warn', () => {
    expect(parseRuntimeConfig({ ...valid, logLevel: 'WARNING' }).logLevel).toBe('warn');
  });

  it('rejects a placeholder that envsubst did not render', () => {
    expect(() =>
      parseRuntimeConfig({ ...valid, apiUrl: '${AGILINA_API_PUBLIC_URL}' }),
    ).toThrowError(RuntimeConfigError, /apiUrl was not rendered/);
  });

  it('reports every problem at once', () => {
    expect(() => parseRuntimeConfig({ logLevel: 'loud' })).toThrowError(
      RuntimeConfigError,
      /apiUrl is missing.*keycloak.url is missing.*logLevel must be one of/,
    );
  });
});
