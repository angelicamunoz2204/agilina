import { ApplicationRef, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { NEVER, of, throwError, type Observable } from 'rxjs';

import { TeamDashboardFacade } from './team-dashboard.facade';
import { TeamsPort } from './teams.port';
import { type Team } from '../domain/team';

/** Port double: get() answers the team of each known id and fails for any other. */
class FakeTeamsPort extends TeamsPort {
  readonly requested: string[] = [];
  readonly teams: Record<string, Team> = {
    atlas: { id: 'atlas', name: 'Atlas', role: 'admin' },
    boreal: { id: 'boreal', name: 'Boreal', role: 'admin' },
  };

  listMine(): Observable<readonly Team[]> {
    return NEVER;
  }

  create(): Observable<string> {
    return NEVER;
  }

  get(teamId: string): Observable<Team> {
    this.requested.push(teamId);
    const team = this.teams[teamId];
    return team === undefined ? throwError(() => new Error('403')) : of(team);
  }
}

describe('TeamDashboardFacade', () => {
  let port: FakeTeamsPort;
  let facade: TeamDashboardFacade;

  beforeEach(() => {
    port = new FakeTeamsPort();
    TestBed.configureTestingModule({
      providers: [TeamDashboardFacade, { provide: TeamsPort, useValue: port }],
    });
    facade = TestBed.inject(TeamDashboardFacade);
  });

  async function stable(): Promise<void> {
    await TestBed.inject(ApplicationRef).whenStable();
  }

  it('asks for nothing until it knows which team to follow', async () => {
    await stable();

    expect(port.requested).toEqual([]);
    expect(facade.team()).toBeNull();
    expect(facade.failed()).toBeFalse();
  });

  it('loads the team of the id it receives', async () => {
    facade.follow(signal('atlas'));
    await stable();

    expect(port.requested).toEqual(['atlas']);
    expect(facade.team()).toEqual({ id: 'atlas', name: 'Atlas', role: 'admin' });
    expect(facade.loading()).toBeFalse();
  });

  it('loads the team again when the id changes', async () => {
    const teamId = signal('atlas');
    facade.follow(teamId);
    await stable();

    teamId.set('boreal');
    await stable();

    expect(port.requested).toEqual(['atlas', 'boreal']);
    expect(facade.team()).toEqual({ id: 'boreal', name: 'Boreal', role: 'admin' });
  });

  it('turns a refused team into the failed state', async () => {
    facade.follow(signal('someone-elses'));
    await stable();

    expect(facade.failed()).toBeTrue();
    expect(facade.team()).toBeNull();
  });
});
