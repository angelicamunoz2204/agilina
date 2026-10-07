import { type EnvironmentProviders, inject, makeEnvironmentProviders } from '@angular/core';
import Keycloak from 'keycloak-js';

import { RUNTIME_CONFIG } from '@core/config/runtime-config';

import { AuthSession } from './auth-session';
import { KEYCLOAK_CLIENT_FACTORY, KeycloakAuthSession } from './keycloak-auth-session';

/** The session of the person, with Keycloak as the identity provider (one realm per tenant). */
export function provideAuth(): EnvironmentProviders {
  return makeEnvironmentProviders([
    {
      provide: KEYCLOAK_CLIENT_FACTORY,
      useFactory: () => {
        const { url, clientId } = inject(RUNTIME_CONFIG).keycloak;
        return (realm: string) => new Keycloak({ url, realm, clientId });
      },
    },
    { provide: AuthSession, useClass: KeycloakAuthSession },
  ]);
}
