import { inject, Injectable } from '@angular/core';

import { AuthSession } from '@core/auth/auth-session';
import { TenantContext } from '@core/tenant/tenant-context';

import { type LoginRedirectPort } from '../application/login-redirect.port';

/**
 * Adapter of the login redirect over the session of the application (`core/auth`): the
 * sign-in itself, with Keycloak, is done there once for the whole application.
 */
@Injectable()
export class SessionLoginAdapter implements LoginRedirectPort {
  private readonly session = inject(AuthSession);
  private readonly tenant = inject(TenantContext);

  redirect(loginHint?: string): Promise<void> {
    return this.session.signIn({
      // After signing in the person lands on their teams, in their organization.
      returnUrl: this.tenant.url('teams'),
      ...(loginHint !== undefined && { loginHint }),
    });
  }
}
