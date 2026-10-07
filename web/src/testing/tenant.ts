import {
  type EnvironmentProviders,
  inject,
  type Provider,
  provideEnvironmentInitializer,
} from '@angular/core';
import { type Observable, of, throwError } from 'rxjs';

import { TenantContext } from '@core/tenant/tenant-context';
import { TenantNotFoundError } from '@core/tenant/tenant-not-found-error';
import { type TenantInfo, TenantPort } from '@core/tenant/tenant.port';

/** The application in the address of a tenant (`/acme/...`): what the route guard does. */
export function provideTestTenant(slug = 'acme'): EnvironmentProviders {
  return provideEnvironmentInitializer(() => {
    inject(TenantContext).set(slug);
  });
}

/** Catalog double: it knows the tenants the test gives it and says "not found" to the rest. */
export class FakeTenantPort extends TenantPort {
  readonly asked: string[] = [];
  failure: unknown = null;

  constructor(private readonly known: readonly string[] = ['acme', 'ecomoda']) {
    super();
  }

  find(slug: string): Observable<TenantInfo> {
    this.asked.push(slug);
    if (this.failure !== null) {
      return throwError(() => this.failure);
    }
    return this.known.includes(slug)
      ? of({ slug, displayName: slug, language: 'es' })
      : throwError(() => new TenantNotFoundError(slug));
  }
}

export function provideFakeTenantPort(port: FakeTenantPort = new FakeTenantPort()): Provider {
  return { provide: TenantPort, useValue: port };
}
