import { HttpClient, HttpContext, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, type Observable, throwError } from 'rxjs';

import { WITHOUT_SESSION } from '@core/auth/auth.interceptor';
import { RUNTIME_CONFIG } from '@core/config/runtime-config';

import { TenantNotFoundError } from './tenant-not-found-error';
import { type TenantInfo, type TenantPort } from './tenant.port';

/** Body of GET /v1/tenant, exactly as the API sends it. */
interface TenantResponse {
  slug: string;
  display_name: string;
  language: 'es' | 'en';
}

/** HTTP adapter of the catalog of tenants. */
@Injectable()
export class HttpTenantApi implements TenantPort {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(RUNTIME_CONFIG).apiUrl;

  find(slug: string): Observable<TenantInfo> {
    // The tenant is asked about before anyone signs in (and before it is known that it has a
    // realm to sign in to), so this request carries no session; the tenant goes in the
    // header the interceptor sets from the address.
    return this.http
      .get<TenantResponse>(`${this.baseUrl}/v1/tenant`, {
        context: new HttpContext().set(WITHOUT_SESSION, true),
      })
      .pipe(
        map((response) => ({
          slug: response.slug,
          displayName: response.display_name,
          language: response.language,
        })),
        catchError((error: unknown) =>
          throwError(() =>
            error instanceof HttpErrorResponse && error.status === 404
              ? new TenantNotFoundError(`The tenant ${slug} is not there`)
              : error,
          ),
        ),
      );
  }
}
