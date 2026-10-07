import { inject } from '@angular/core';
import { type CanActivateFn, type CanMatchFn, Router, type UrlSegment } from '@angular/router';
import { catchError, firstValueFrom, map, of } from 'rxjs';

import { TenantContext } from './tenant-context';
import { TenantNotFoundError } from './tenant-not-found-error';
import { isValidTenantSlug } from './tenant-slug';
import { TenantPort } from './tenant.port';

/**
 * Only an address whose first segment can be a tenant's name opens the tenant's routes; any
 * other (`/`, `/Acme`, `/ac-me`) falls through to the page that is not found.
 */
export const tenantMatch: CanMatchFn = (route, segments: UrlSegment[]) => {
  const first = segments[0]?.path;
  return first !== undefined && isValidTenantSlug(first);
};

/**
 * Records the tenant of the address before anything below it asks for it, and asks the
 * platform whether it exists: a name that looks right but belongs to nobody (or to a suspended
 * tenant) is the page that is not found, before anyone is taken to sign in to a realm that is
 * not there. If the platform cannot be asked the person goes on: the screen will say so.
 */
export const tenantGuard: CanActivateFn = async (route) => {
  const slug = route.paramMap.get('tenant');
  if (slug === null) {
    return false;
  }
  const tenants = inject(TenantContext);
  const port = inject(TenantPort);
  const router = inject(Router);
  tenants.set(slug);
  return firstValueFrom(
    port.find(slug).pipe(
      map(() => true),
      catchError((error: unknown) =>
        of(error instanceof TenantNotFoundError ? router.createUrlTree(['/not-found']) : true),
      ),
    ),
  );
};
