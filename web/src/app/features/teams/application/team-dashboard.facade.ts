import { computed, inject, Injectable, signal, type Signal } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';

import { TeamsPort } from './teams.port';
import { type Team } from '../domain/team';
import { failureKindOf, type TeamFailureKind } from '../domain/team-failure';

/**
 * State of a team's dashboard: the team whose id the page receives. Provided by the
 * page, so it lives and dies with it.
 *
 * A failed request (a team the user does not belong to, for example) becomes the
 * `failed` state; the HTTP interceptor has already logged it, so it is not logged
 * again here.
 */
@Injectable()
export class TeamDashboardFacade {
  private readonly teamsPort = inject(TeamsPort);
  private readonly teamId = signal<Signal<string> | null>(null);
  private readonly current = rxResource({
    params: () => this.teamId()?.(),
    stream: ({ params }) => this.teamsPort.get(params),
  });

  readonly team = computed<Team | null>(() =>
    this.current.hasValue() ? this.current.value() : null,
  );
  readonly loading = this.current.isLoading;

  readonly failed = computed(() => this.current.status() === 'error');
  /** What went wrong, when the team could not be opened. */
  readonly problem = computed<TeamFailureKind | null>(() =>
    this.failed() ? failureKindOf(this.current.error()) : null,
  );

  /** Loads the team of this id, and loads it again whenever the id changes. */
  follow(teamId: Signal<string>): void {
    this.teamId.set(teamId);
  }
}
