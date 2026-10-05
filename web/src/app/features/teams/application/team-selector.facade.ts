import { computed, inject, Injectable } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';

import { TeamsPort } from './teams.port';
import { type Team } from '../domain/team';

/**
 * State of the team selector: the teams of the signed-in user. Provided by the page,
 * so it lives and dies with it.
 *
 * A failed request becomes the `failed` state; the HTTP interceptor has already
 * logged it, so it is not logged again here.
 */
@Injectable()
export class TeamSelectorFacade {
  private readonly teamsPort = inject(TeamsPort);
  private readonly mine = rxResource({ stream: () => this.teamsPort.listMine() });

  /** Null until the API answers; an empty list means the user has no team yet. */
  readonly teams = computed<readonly Team[] | null>(() =>
    this.mine.hasValue() ? this.mine.value() : null,
  );
  readonly loading = this.mine.isLoading;
  readonly failed = computed(() => this.mine.status() === 'error');
}
