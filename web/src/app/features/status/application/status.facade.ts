import { Injectable, inject, signal } from '@angular/core';

import { ServiceStatus } from '../domain/service-status';
import { HealthPort } from './health.port';

/** State of the status screen: what the presentation layer reads and triggers. */
@Injectable({ providedIn: 'root' })
export class StatusFacade {
  private readonly health = inject(HealthPort);

  readonly status = signal<ServiceStatus | null>(null);
  readonly checking = signal(false);
  readonly failed = signal(false);

  refresh(): void {
    this.checking.set(true);
    this.failed.set(false);

    this.health.check().subscribe({
      next: (status) => {
        this.status.set(status);
        this.checking.set(false);
      },
      error: () => {
        this.status.set(null);
        this.failed.set(true);
        this.checking.set(false);
      },
    });
  }
}
