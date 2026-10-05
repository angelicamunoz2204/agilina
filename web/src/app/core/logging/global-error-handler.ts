import { type ErrorHandler, Injectable, inject } from '@angular/core';

import { Logger } from './logger';

/**
 * Last line of defence: every error that nobody handled ends up here (together
 * with the window errors that provideBrowserGlobalErrorListeners forwards), so no
 * failure is lost in silence.
 */
@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  private readonly logger = inject(Logger);

  handleError(error: unknown): void {
    this.logger.error('Unhandled error', error);
  }
}
