import { computed, inject, Injectable } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';

import { HealthPort } from './health.port';
import { type ServiceStatus } from '../domain/service-status';

/**
 * State of the status screen: what the presentation reads and triggers. Provided
 * by the page, so it lives and dies with it.
 *
 * A failed check becomes the `failed` state; the HTTP interceptor has already
 * logged it, so it is not logged again here.
 */
@Injectable()
export class StatusFacade {
  private readonly health = inject(HealthPort);
  private readonly probe = rxResource({ stream: () => this.health.check() });

  readonly serviceStatus = computed<ServiceStatus | null>(() =>
    this.probe.hasValue() ? this.probe.value() : null,
  );
  readonly checking = this.probe.isLoading;
  readonly failed = computed(() => this.probe.status() === 'error');

  refresh(): void {
    this.probe.reload();
  }
}
