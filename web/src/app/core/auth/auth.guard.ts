import { inject } from '@angular/core';
import { type CanActivateFn, Router } from '@angular/router';

import { AuthSession } from './auth-session';

/**
 * Lets the signed-in through; takes everybody else to sign in and brings them back to the
 * very page they asked for. It is comfort, not security: the API decides who sees what.
 */
export const authGuard: CanActivateFn = (route, state) => {
  return inject(AuthSession).ensureSignedIn(state.url);
};

/**
 * The entrance of the product (`/`): whoever is signed in goes to their teams, and whoever is
 * not goes to sign in, and then to their teams.
 */
export const entranceGuard: CanActivateFn = async () => {
  // Both are injected before the first `await`: after it there is no injection context.
  const session = inject(AuthSession);
  const router = inject(Router);
  const signedIn = await session.ensureSignedIn('/teams');
  return signedIn ? router.createUrlTree(['/teams']) : false;
};
