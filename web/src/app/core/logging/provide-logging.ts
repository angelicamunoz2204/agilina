import {
  ErrorHandler,
  makeEnvironmentProviders,
  provideBrowserGlobalErrorListeners,
  type EnvironmentProviders,
} from '@angular/core';

import { ConsoleLogger } from './console-logger';
import { GlobalErrorHandler } from './global-error-handler';
import { Logger } from './logger';

/** Binds the Logger port and routes every unhandled error to it. */
export function provideLogging(): EnvironmentProviders {
  return makeEnvironmentProviders([
    provideBrowserGlobalErrorListeners(),
    { provide: Logger, useClass: ConsoleLogger },
    { provide: ErrorHandler, useClass: GlobalErrorHandler },
  ]);
}
