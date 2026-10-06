import { Component, computed, inject, input, type OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslocoDirective } from '@jsverse/transloco';

import { Button } from '@shared/ui/button';

import { problemMessageKey } from './problem-message';
import { TeamDashboardFacade } from '../application/team-dashboard.facade';

/**
 * Dashboard of a team. For now a placeholder that shows the team's name and, to an admin, the
 * way to the team settings. Hiding that link from a member is a convenience: the settings ask
 * the API, which refuses a member.
 */
@Component({
  selector: 'agl-team-dashboard-page',
  imports: [RouterLink, TranslocoDirective, Button],
  providers: [TeamDashboardFacade],
  templateUrl: './team-dashboard-page.html',
})
export class TeamDashboardPage implements OnInit {
  /** The :teamId of the route, bound by the router (withComponentInputBinding). */
  readonly teamId = input.required<string>();

  private readonly facade = inject(TeamDashboardFacade);

  protected readonly team = this.facade.team;
  protected readonly loading = this.facade.loading;
  protected readonly problemMessage = computed(() => problemMessageKey(this.facade.problem()));

  ngOnInit(): void {
    this.facade.follow(this.teamId);
  }
}
