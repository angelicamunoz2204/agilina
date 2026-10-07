import { inject, Injectable } from '@angular/core';

import { AuthSession } from '@core/auth/auth-session';

import { type LoginRedirectPort } from '../application/login-redirect.port';

/** Where the person lands after signing in: their teams. */
const AFTER_SIGN_IN = '/teams';

/**
 * Adapter of the login redirect over the session of the application (`core/auth`): the
 * sign-in itself, with Keycloak, is done there once for the whole application.
 */
@Injectable()
export class SessionLoginAdapter implements LoginRedirectPort {
  private readonly session = inject(AuthSession);

  redirect(loginHint?: string): Promise<void> {
    return this.session.signIn({
      returnUrl: AFTER_SIGN_IN,
      ...(loginHint !== undefined && { loginHint }),
    });
  }
}
