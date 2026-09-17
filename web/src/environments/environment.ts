/**
 * Configuración de producción.
 *
 * En la nube la aplicación se sirve detrás del mismo dominio que la API, de
 * modo que las rutas relativas evitan tener que recompilar por entorno. Eso
 * supone un proxy inverso que enrute `/api` hacia la API y `/auth` hacia
 * Keycloak, recortando el prefijo; se configura con el despliegue (HU-38).
 */
export const environment = {
  produccion: true,
  apiUrl: '/api',
  keycloak: {
    url: '/auth',
    realm: 'agilina',
    clientId: 'agilina-web',
  },
};
