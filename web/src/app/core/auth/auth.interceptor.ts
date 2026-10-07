import { DOCUMENT } from '@angular/common';
import { HttpErrorResponse, type HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, from, switchMap, throwError } from 'rxjs';

import { RUNTIME_CONFIG } from '@core/config/runtime-config';

import { AuthSession } from './auth-session';

/**
 * Sends the access token to the API, and only to the API: never to Keycloak or to any other
 * host. When the API answers 401 (no token, or one that expired or was refused), the person
 * is taken to sign in and comes back to where they were. The error keeps propagating.
 */
export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const apiUrl = inject(RUNTIME_CONFIG).apiUrl;
  if (!request.url.startsWith(`${apiUrl}/`)) {
    return next(request);
  }
  const session = inject(AuthSession);
  const location = inject(DOCUMENT).location;

  return from(session.accessToken()).pipe(
    switchMap((token) =>
      next(
        token === null
          ? request
          : request.clone({ setHeaders: { Authorization: `Bearer ${token}` } }),
      ),
    ),
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && error.status === 401) {
        void session.signIn({ returnUrl: `${location.pathname}${location.search}` });
      }
      return throwError(() => error);
    }),
  );
};
