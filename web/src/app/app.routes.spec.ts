import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { NEVER, type Observable } from 'rxjs';

import { TeamsPort } from '@features/teams/application/teams.port';
import { type Team } from '@features/teams/domain/team';
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

describe('routes', () => {
  let port: SilentTeamsPort;
  let harness: RouterTestingHarness;

  beforeEach(async () => {
    port = new SilentTeamsPort();
    TestBed.configureTestingModule({
      providers: [
        provideTestI18n(),
        provideRouter(routes, withComponentInputBinding()),
        { provide: TeamsPort, useValue: port },
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
});
