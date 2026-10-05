import { type Observable } from 'rxjs';

import { type ServiceStatus } from '../domain/service-status';

/**
 * Port towards the API health probe. An abstract class so that it doubles as the
 * injection token; the HTTP adapter is bound in app.config.ts.
 */
export abstract class HealthPort {
  abstract check(): Observable<ServiceStatus>;
}
