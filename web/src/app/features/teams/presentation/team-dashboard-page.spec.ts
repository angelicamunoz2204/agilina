import { TestBed } from '@angular/core/testing';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { NEVER, of, Subject, throwError, type Observable } from 'rxjs';

import { provideTestI18n } from '@testing/i18n';

import { TeamDashboardPage } from './team-dashboard-page';
import { TeamsPort } from '../application/teams.port';
import { type Team } from '../domain/team';

/** Port double: get() answers the known teams, keeps 'slow' pending and refuses the rest. */
class FakeTeamsPort extends TeamsPort {
  readonly requested: string[] = [];
  readonly known: readonly Team[] = [
    { id: 'atlas', name: 'Atlas' },
    { id: 'boreal', name: 'Boreal' },
  ];

  listMine(): Observable<readonly Team[]> {
    return NEVER;
  }

  create(): Observable<string> {
    return NEVER;
  }

  get(teamId: string): Observable<Team> {
    this.requested.push(teamId);
    if (teamId === 'slow') {
      return new Subject<Team>();
    }
    const team = this.known.find((candidate) => candidate.id === teamId);
    return team === undefined ? throwError(() => new Error('403')) : of(team);
  }
}

describe('TeamDashboardPage', () => {
  let port: FakeTeamsPort;
  let harness: RouterTestingHarness;

  beforeEach(async () => {
    port = new FakeTeamsPort();
    TestBed.configureTestingModule({
      providers: [
        provideTestI18n(),
        provideRouter(
          [{ path: 'teams/:teamId', component: TeamDashboardPage }],
          withComponentInputBinding(),
        ),
        { provide: TeamsPort, useValue: port },
      ],
    });
    harness = await RouterTestingHarness.create();
  });

  async function open(url: string): Promise<HTMLElement> {
    await harness.navigateByUrl(url);
    await harness.fixture.whenStable();
    return harness.routeNativeElement!;
  }

  it('shows the name of the team of the :teamId', async () => {
    const page = await open('/teams/atlas');

    expect(port.requested).toEqual(['atlas']);
    expect(page.querySelector('h1')?.textContent).toBe('Atlas');
  });

  it('loads the other team when the :teamId changes', async () => {
    await open('/teams/atlas');

    const page = await open('/teams/boreal');

    expect(port.requested).toEqual(['atlas', 'boreal']);
    expect(page.querySelector('h1')?.textContent).toBe('Boreal');
  });

  it('says it is loading while the API has not answered', async () => {
    // Not whenStable: the request stays pending, so the page never settles.
    await harness.navigateByUrl('/teams/slow');
    TestBed.tick();
    const page = harness.routeNativeElement!;

    expect(page.textContent).toContain('Cargando el equipo…');
    expect(page.querySelector('h1')).toBeNull();
  });

  it('shows a translated message when the API refuses the team', async () => {
    const page = await open('/teams/someone-elses');

    expect(page.querySelector('[role="alert"]')?.textContent).toBe('No se pudo abrir este equipo.');
    expect(page.querySelector('h1')).toBeNull();
  });
});
