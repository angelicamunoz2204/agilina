import { Observable } from 'rxjs';

import { ServiceStatus } from '../domain/service-status';

/**
 * Port towards the API health probe. An abstract class so that it can be used
 * as an injection token; the HTTP adapter is bound in `app.config.ts`.
 *
 * The ceremony controls do not go through the API: they travel through the
 * LiveKit data channel straight to the worker.
 */
export abstract class HealthPort {
  abstract check(): Observable<ServiceStatus>;
}
