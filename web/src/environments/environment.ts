/**
 * Production settings.
 *
 * In the cloud the application is served behind the same domain as the API, so
 * relative paths avoid recompiling per environment. That assumes a reverse
 * proxy routing `/api` to the API and `/auth` to Keycloak, stripping the
 * prefix; it is configured with the deployment (HU-38).
 */
export const environment = {
  production: true,
  apiUrl: '/api',
  keycloak: {
    url: '/auth',
    realm: 'agilina',
    clientId: 'agilina-web',
  },
};
