/** Local development settings: each service on its own port. */
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  keycloak: {
    url: 'http://localhost:8080',
    realm: 'agilina',
    clientId: 'agilina-web',
  },
};
