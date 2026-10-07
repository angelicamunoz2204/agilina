import { computed, inject, Injectable } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';

import { TeamsPort } from './teams.port';
import { type Team } from '../domain/team';
import { failureKindOf, type TeamFailureKind } from '../domain/team-failure';

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
  /** The team to enter straight away: when the user belongs to exactly one there is nothing to
   * choose (HU-03). Null while the list is loading, and with none or several teams. */
  readonly onlyTeam = computed<Team | null>(() => {
    const teams = this.teams();
    return teams?.length === 1 ? (teams[0] ?? null) : null;
  });
  readonly loading = this.mine.isLoading;
  readonly failed = computed(() => this.mine.status() === 'error');
  /** What went wrong, when the list could not be loaded. */
  readonly problem = computed<TeamFailureKind | null>(() =>
    this.failed() ? failureKindOf(this.mine.error()) : null,
  );
}
