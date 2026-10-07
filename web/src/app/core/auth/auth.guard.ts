import { inject } from '@angular/core';
import { type CanActivateFn, Router } from '@angular/router';

import { TenantContext } from '@core/tenant/tenant-context';

import { AuthSession } from './auth-session';

/**
 * Lets the signed-in through; takes everybody else to sign in and brings them back to the
 * very page they asked for. It is comfort, not security: the API decides who sees what.
 */
export const authGuard: CanActivateFn = (route, state) => {
  return inject(AuthSession).ensureSignedIn(state.url);
};

/**
 * The entrance of a tenant (`/acme`): whoever is signed in goes to their teams, and whoever is
 * not goes to sign in, and then to their teams.
 */
export const entranceGuard: CanActivateFn = async () => {
  // Everything is injected before the first `await`: after it there is no injection context.
  const session = inject(AuthSession);
  const router = inject(Router);
  const tenant = inject(TenantContext);
  const signedIn = await session.ensureSignedIn(tenant.url('teams'));
  return signedIn ? router.createUrlTree(tenant.path('teams')) : false;
};
