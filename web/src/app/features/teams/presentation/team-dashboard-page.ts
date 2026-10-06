import { Component, computed, inject, input, type OnInit } from '@angular/core';
import { TranslocoDirective } from '@jsverse/transloco';

import { problemMessageKey } from './problem-message';
import { TeamDashboardFacade } from '../application/team-dashboard.facade';

/** Dashboard of a team. For now a placeholder that only shows the team's name. */
@Component({
  selector: 'agl-team-dashboard-page',
  imports: [TranslocoDirective],
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
