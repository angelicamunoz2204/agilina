import { loadRuntimeConfig } from './load-runtime-config';
import { RuntimeConfigError } from './runtime-config';

describe('loadRuntimeConfig', () => {
  it('loads and validates config.json', async () => {
    const body = {
      apiUrl: '/api',
      keycloak: { url: '/auth', realm: 'agilina', clientId: 'agilina-web' },
      logLevel: 'error',
    };
    const fetchFn = jasmine
      .createSpy<typeof fetch>('fetch')
      .and.resolveTo(new Response(JSON.stringify(body)));

    const config = await loadRuntimeConfig(fetchFn);

    expect(config.apiUrl).toBe('/api');
    expect(fetchFn).toHaveBeenCalledWith('config.json', { cache: 'no-store' });
  });

  it('fails when config.json is not served', async () => {
    const fetchFn = jasmine
      .createSpy<typeof fetch>('fetch')
      .and.resolveTo(new Response('', { status: 404 }));

    await expectAsync(loadRuntimeConfig(fetchFn)).toBeRejectedWithError(
      RuntimeConfigError,
      /HTTP 404/,
    );
  });
});
