import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { type ApplicationConfig } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';

import { RUNTIME_CONFIG, type RuntimeConfig } from '@core/config/runtime-config';
import { httpErrorLoggingInterceptor } from '@core/http/http-error-logging.interceptor';
import { provideI18n } from '@core/i18n/provide-i18n';
import { provideLogging } from '@core/logging/provide-logging';
import { InvitationPort } from '@features/identity/application/invitation.port';
import { LoginRedirectPort } from '@features/identity/application/login-redirect.port';
import { HttpInvitationApi } from '@features/identity/infrastructure/http-invitation.api';
import { KeycloakLoginAdapter } from '@features/identity/infrastructure/keycloak-login.adapter';
import { HealthPort } from '@features/status/application/health.port';
import { HttpHealthApi } from '@features/status/infrastructure/http-health.api';
import { TeamsPort } from '@features/teams/application/teams.port';
import { HttpTeamsApi } from '@features/teams/infrastructure/http-teams.api';

import { routes } from './app.routes';

/**
 * Composition root of the web application: the only place that knows which
 * adapter serves each port. Zoneless and OnPush are the Angular 22 defaults.
 */
export function createAppConfig(runtimeConfig: RuntimeConfig): ApplicationConfig {
  return {
    providers: [
      { provide: RUNTIME_CONFIG, useValue: runtimeConfig },
      provideLogging(),
      provideRouter(routes, withComponentInputBinding()),
      provideHttpClient(withInterceptors([httpErrorLoggingInterceptor])),
      provideI18n(),

      // Ports of the features, bound to their adapters.
      { provide: HealthPort, useClass: HttpHealthApi },
      { provide: InvitationPort, useClass: HttpInvitationApi },
      { provide: LoginRedirectPort, useClass: KeycloakLoginAdapter },
      { provide: TeamsPort, useClass: HttpTeamsApi },
    ],
  };
}
