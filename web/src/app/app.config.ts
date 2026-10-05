import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { type ApplicationConfig } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';

import { RUNTIME_CONFIG, type RuntimeConfig } from '@core/config/runtime-config';
import { httpErrorLoggingInterceptor } from '@core/http/http-error-logging.interceptor';
import { provideI18n } from '@core/i18n/provide-i18n';
import { provideLogging } from '@core/logging/provide-logging';
import { HealthPort } from '@features/status/application/health.port';
import { HttpHealthApi } from '@features/status/infrastructure/http-health.api';

import { routes } from './app.routes';

/**
 * Composition root of the web application: the only place that knows which
 * adapter serves each port. Zoneless and OnPush are the Angular 22 defaults.
 */
export function createAppConfig(runtimeConfig: RuntimeConfig): ApplicationConfig {
  return {
    providers: [
      { provide: RUNTIME_CONFIG, useValue: runtimeConfig },
      provideLogging(),
      provideRouter(routes, withComponentInputBinding()),
      provideHttpClient(withInterceptors([httpErrorLoggingInterceptor])),
      provideI18n(),

      // Ports of the features, bound to their adapters.
      { provide: HealthPort, useClass: HttpHealthApi },
    ],
  };
}
