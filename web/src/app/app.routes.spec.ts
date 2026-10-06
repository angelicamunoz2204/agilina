import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { NEVER, type Observable } from 'rxjs';

import { TeamMembersPort } from '@features/teams/application/team-members.port';
import { TeamsPort } from '@features/teams/application/teams.port';
import { type Team } from '@features/teams/domain/team';
import { type TeamMembers } from '@features/teams/domain/team-member';
import { provideTestI18n } from '@testing/i18n';

import { routes } from './app.routes';

/** Port double that never answers: these tests only look at which screen opens. */
class SilentTeamsPort extends TeamsPort {
  readonly requested: string[] = [];

  listMine(): Observable<readonly Team[]> {
    return NEVER;
  }

  create(): Observable<string> {
    return NEVER;
  }

  get(teamId: string): Observable<Team> {
    this.requested.push(teamId);
    return NEVER;
  }
}

/** Port double that never answers and remembers which team's members were asked for. */
class SilentTeamMembersPort extends TeamMembersPort {
  readonly requested: string[] = [];

  list(teamId: string): Observable<TeamMembers> {
    this.requested.push(teamId);
    return NEVER;
  }

  invite(): Observable<never> {
    return NEVER;
  }

  changeRole(): Observable<never> {
    return NEVER;
  }

  remove(): Observable<never> {
    return NEVER;
  }
}

describe('routes', () => {
  let port: SilentTeamsPort;
  let members: SilentTeamMembersPort;
  let harness: RouterTestingHarness;

  beforeEach(async () => {
    port = new SilentTeamsPort();
    members = new SilentTeamMembersPort();
    TestBed.configureTestingModule({
      providers: [
        provideTestI18n(),
        provideRouter(routes, withComponentInputBinding()),
        { provide: TeamsPort, useValue: port },
        { provide: TeamMembersPort, useValue: members },
      ],
    });
    harness = await RouterTestingHarness.create();
  });

  /** The layout the route opens and the screen inside it. */
  async function screenAt(url: string): Promise<string | undefined> {
    await harness.navigateByUrl(url);
    const layout = harness.routeNativeElement;
    const screen = layout?.querySelector('router-outlet + *');
    return `${layout?.tagName.toLowerCase()} > ${screen?.tagName.toLowerCase()}`;
  }

  it('opens the team selector at /teams', async () => {
    expect(await screenAt('/teams')).toBe('agl-centered-layout > agl-team-selector-page');
  });

  it('opens the creation form at /teams/new, not a team called "new"', async () => {
    expect(await screenAt('/teams/new')).toBe('agl-centered-layout > agl-create-team-page');
    expect(port.requested).toEqual([]);
  });

  it('opens the dashboard of the team at /teams/:teamId with that id', async () => {
    expect(await screenAt('/teams/team-1')).toBe('agl-app-shell > agl-team-dashboard-page');
    TestBed.tick();

    expect(port.requested).toEqual(['team-1']);
    expect(TestBed.inject(Router).url).toBe('/teams/team-1');
  });

  it('opens the settings of the team at /teams/:teamId/settings, without a guard', async () => {
    expect(await screenAt('/teams/team-1/settings')).toBe('agl-app-shell > agl-team-settings-page');
    TestBed.tick();

    expect(members.requested).toEqual(['team-1']);
    expect(port.requested).toEqual([]);
    expect(TestBed.inject(Router).url).toBe('/teams/team-1/settings');
  });
});
