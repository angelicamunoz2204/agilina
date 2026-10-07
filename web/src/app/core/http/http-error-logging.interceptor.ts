import { HttpErrorResponse, type HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { tap } from 'rxjs';

import { readApiError } from './api-error';
import { Logger } from '../logging/logger';

/**
 * Logs every failed HTTP request once, here, so that adapters and facades only
 * decide what the user sees. The error keeps propagating: logging is not handling.
 * Only method, URL without query, status and, when the API sent them, the error `code` and
 * `request_id` are logged: never bodies or headers, which may carry tokens or personal data.
 * The request id is what the API's own log is searched with.
 */
export const httpErrorLoggingInterceptor: HttpInterceptorFn = (request, next) => {
  const logger = inject(Logger);
  return next(request).pipe(
    tap({
      error: (error: unknown) => {
        const apiError = readApiError(error instanceof HttpErrorResponse ? error.error : undefined);
        logger.error('HTTP request failed', error, {
          method: request.method,
          url: withoutQuery(request.url),
          status: error instanceof HttpErrorResponse ? error.status : undefined,
          ...(apiError && { code: apiError.code, requestId: apiError.requestId }),
        });
      },
    }),
  );
};

/** A query string may carry tokens (an activation link, for example). */
function withoutQuery(url: string): string {
  return url.split(/[?#]/, 1)[0] ?? url;
}
