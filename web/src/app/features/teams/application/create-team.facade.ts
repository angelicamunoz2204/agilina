import { inject, Injectable, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { TeamsPort } from './teams.port';

/**
 * State of the team creation: whether it is saving and whether the last attempt
 * failed. Provided by the page, so it lives and dies with it.
 *
 * A failed request becomes the `failed` state; the HTTP interceptor has already
 * logged it, so it is not logged again here.
 */
@Injectable()
export class CreateTeamFacade {
  private readonly teamsPort = inject(TeamsPort);
  private readonly isSaving = signal(false);
  private readonly hasFailed = signal(false);

  readonly saving = this.isSaving.asReadonly();
  readonly failed = this.hasFailed.asReadonly();

  /** Creates the team and resolves to its id, or to null if the API refused it. */
  async create(name: string): Promise<string | null> {
    this.isSaving.set(true);
    this.hasFailed.set(false);
    try {
      return await firstValueFrom(this.teamsPort.create(name));
    } catch {
      this.hasFailed.set(true);
      return null;
    } finally {
      this.isSaving.set(false);
    }
  }
}
