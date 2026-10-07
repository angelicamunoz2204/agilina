import { type EnvironmentProviders, inject, makeEnvironmentProviders } from '@angular/core';
import Keycloak from 'keycloak-js';

import { RUNTIME_CONFIG } from '@core/config/runtime-config';

import { AuthSession } from './auth-session';
import { KEYCLOAK_CLIENT, KeycloakAuthSession } from './keycloak-auth-session';

/** The session of the person, with Keycloak as the identity provider. */
export function provideAuth(): EnvironmentProviders {
  return makeEnvironmentProviders([
    {
      provide: KEYCLOAK_CLIENT,
      useFactory: () => {
        const { url, realm, clientId } = inject(RUNTIME_CONFIG).keycloak;
        return new Keycloak({ url, realm, clientId });
      },
    },
    { provide: AuthSession, useClass: KeycloakAuthSession },
  ]);
}
