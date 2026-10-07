import { Component, computed, effect, inject } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { TranslocoDirective } from '@jsverse/transloco';

import { Button } from '@shared/ui/button';

import { problemMessageKey } from './problem-message';
import { TeamSelectorFacade } from '../application/team-selector.facade';

/** Team selector: the teams of the user, to enter one, and the way to create a new one. */
@Component({
  selector: 'agl-team-selector-page',
  imports: [RouterLink, TranslocoDirective, Button],
  providers: [TeamSelectorFacade],
  templateUrl: './team-selector-page.html',
})
export class TeamSelectorPage {
  private readonly facade = inject(TeamSelectorFacade);
  private readonly router = inject(Router);

  protected readonly teams = this.facade.teams;
  protected readonly loading = this.facade.loading;
  protected readonly problemMessage = computed(() => problemMessageKey(this.facade.problem()));

  /** With a single team there is nothing to choose: go in, replacing this page in the history
   * so that "back" does not bring the person here just to be sent on again. */
  private readonly enterTheOnlyTeam = effect(() => {
    const team = this.facade.onlyTeam();
    if (team !== null) {
      void this.router.navigate(['/teams', team.id], { replaceUrl: true });
    }
  });
}
