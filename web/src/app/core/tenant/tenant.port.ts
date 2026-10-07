import { type Observable } from 'rxjs';

/** What the platform says about an organization that exists (`GET /v1/tenant`). */
export interface TenantInfo {
  readonly slug: string;
  readonly displayName: string;
  readonly language: 'es' | 'en';
}

/**
 * Port towards the catalog of tenants of the platform. An abstract class so that it doubles as
 * the injection token; the HTTP adapter is bound in app.config.ts. It fails with a
 * `TenantNotFoundError` when the tenant is not there, and with any other error when the
 * platform could not be asked.
 */
export abstract class TenantPort {
  abstract find(slug: string): Observable<TenantInfo>;
}
