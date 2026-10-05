import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslocoDirective } from '@jsverse/transloco';

import { TeamSelectorFacade } from '../application/team-selector.facade';

/** Team selector: the teams of the user, to enter one, and the way to create a new one. */
@Component({
  selector: 'agl-team-selector-page',
  imports: [RouterLink, TranslocoDirective],
  providers: [TeamSelectorFacade],
  templateUrl: './team-selector-page.html',
  styleUrl: './team-selector-page.scss',
})
export class TeamSelectorPage {
  private readonly facade = inject(TeamSelectorFacade);

  protected readonly teams = this.facade.teams;
  protected readonly loading = this.facade.loading;
  protected readonly failed = this.facade.failed;
}
