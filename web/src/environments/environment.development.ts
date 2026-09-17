/** Configuración de desarrollo local: cada servicio en su propio puerto. */
export const environment = {
  produccion: false,
  apiUrl: 'http://localhost:8000',
  keycloak: {
    url: 'http://localhost:8080',
    realm: 'agilina',
    clientId: 'agilina-web',
  },
};
