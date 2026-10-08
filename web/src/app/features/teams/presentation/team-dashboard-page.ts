import { Component, computed, inject, input, type OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslocoDirective } from '@jsverse/transloco';

import { TenantContext } from '@core/tenant/tenant-context';
import { Button } from '@shared/ui/button';
import { formatCalendarDate } from '@shared/utils/local-date-time';

import { problemMessageKey } from './problem-message';
import { ActiveSprintFacade } from '../application/active-sprint.facade';
import { TeamDashboardFacade } from '../application/team-dashboard.facade';
import { TeamShellFacade } from '../application/team-shell.facade';

/**
 * Dashboard of a team. For now a placeholder that shows the team's name, the day of its active
 * sprint ("day N of M", as the API computes it) and, to an admin, the way to the team settings.
 * Hiding that link from a member is a convenience: the settings ask the API, which refuses a
 * member. If the sprint cannot be read, its line is left out and the rest still shows.
 */
@Component({
  selector: 'agl-team-dashboard-page',
  imports: [RouterLink, TranslocoDirective, Button],
  providers: [TeamDashboardFacade, ActiveSprintFacade, TeamShellFacade],
  templateUrl: './team-dashboard-page.html',
})
export class TeamDashboardPage implements OnInit {
  /** The :teamId of the route, bound by the router (withComponentInputBinding). */
  readonly teamId = input.required<string>();

  private readonly facade = inject(TeamDashboardFacade);
  private readonly sprintFacade = inject(ActiveSprintFacade);
  private readonly shell = inject(TeamShellFacade);
  protected readonly tenant = inject(TenantContext);

  protected readonly team = this.facade.team;
  protected readonly loading = this.facade.loading;
  protected readonly problemMessage = computed(() => problemMessageKey(this.facade.problem()));
  /** Whether the API answered about the sprint: until then, or if it failed, no line shows. */
  protected readonly sprintKnown = this.sprintFacade.known;
  protected readonly sprint = this.sprintFacade.sprint;

  ngOnInit(): void {
    this.facade.follow(this.teamId);
    this.sprintFacade.follow(this.teamId);
    this.shell.follow(this.teamId);
  }

  /** A calendar date, as the person reads it in the active language. */
  protected formatDate(date: string, language: string): string {
    return formatCalendarDate(date, language);
  }
}
