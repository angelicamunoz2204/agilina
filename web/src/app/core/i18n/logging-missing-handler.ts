import { Injectable, inject } from '@angular/core';
import { type TranslocoMissingHandler, type TranslocoMissingHandlerData } from '@jsverse/transloco';

import { Logger } from '../logging/logger';

/**
 * A missing key is logged and shown as the key itself: a visible error on
 * screen is caught in review, a silent blank is not.
 */
@Injectable()
export class LoggingMissingHandler implements TranslocoMissingHandler {
  private readonly logger = inject(Logger);

  handle(key: string, data: TranslocoMissingHandlerData): string {
    this.logger.warn('Missing translation key', { key, language: data.activeLang });
    return key;
  }
}
