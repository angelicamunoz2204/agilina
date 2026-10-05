import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
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

  protected readonly teams = this.facade.teams;
  protected readonly loading = this.facade.loading;
  protected readonly problemMessage = computed(() => problemMessageKey(this.facade.problem()));
}
