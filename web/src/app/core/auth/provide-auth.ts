import {
  type EnvironmentProviders,
  inject,
  makeEnvironmentProviders,
  provideAppInitializer,
} from '@angular/core';
import Keycloak from 'keycloak-js';

import { RUNTIME_CONFIG } from '@core/config/runtime-config';
import { Logger } from '@core/logging/logger';

import { AuthSession } from './auth-session';
import { KEYCLOAK_CLIENT, KeycloakAuthSession } from './keycloak-auth-session';

/**
 * The session of the person, with Keycloak as the identity provider. When the application
 * starts on the way back from signing in, Keycloak's answer is read before the first
 * navigation, so that it never stays in the address bar.
 */
export function provideAuth(): EnvironmentProviders {
  return makeEnvironmentProviders([
    {
      provide: KEYCLOAK_CLIENT,
      useFactory: () => {
        const { url, realm, clientId } = inject(RUNTIME_CONFIG).keycloak;
        return new Keycloak({ url, realm, clientId });
      },
    },
    KeycloakAuthSession,
    { provide: AuthSession, useExisting: KeycloakAuthSession },
    provideAppInitializer(async () => {
      const session = inject(KeycloakAuthSession);
      const logger = inject(Logger);
      try {
        await session.readSignInAnswer();
      } catch (error: unknown) {
        // The application starts anyway: the guard meets the same failure when it asks.
        logger.error('The answer of the sign-in could not be read', error);
      }
    }),
  ]);
}
