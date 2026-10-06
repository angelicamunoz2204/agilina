import { computed, inject, Injectable, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { TeamsPort } from './teams.port';
import { failureKindOf, type TeamFailureKind } from '../domain/team-failure';

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
  private readonly lastProblem = signal<TeamFailureKind | null>(null);

  readonly saving = this.isSaving.asReadonly();
  /** What went wrong in the last attempt, if it failed. */
  readonly problem = this.lastProblem.asReadonly();
  readonly failed = computed(() => this.lastProblem() !== null);

  /** Creates the team and resolves to its id, or to null if the API refused it. */
  async create(name: string): Promise<string | null> {
    this.isSaving.set(true);
    this.lastProblem.set(null);
    try {
      return await firstValueFrom(this.teamsPort.create(name));
    } catch (error: unknown) {
      this.lastProblem.set(failureKindOf(error));
      return null;
    } finally {
      this.isSaving.set(false);
    }
  }
}
