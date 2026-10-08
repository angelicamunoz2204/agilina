import { TestBed } from '@angular/core/testing';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { NEVER, of, Subject, throwError, type Observable } from 'rxjs';

import { provideTestI18n } from '@testing/i18n';
import { aTeam } from '@testing/team';
import { provideTestTenant } from '@testing/tenant';
import { provideStubUsersPort } from '@testing/users';

import { TeamDashboardPage } from './team-dashboard-page';
import { SprintsPort } from '../application/sprints.port';
import { TeamsPort } from '../application/teams.port';
import { type ActiveSprint, type SprintDay } from '../domain/active-sprint';
import { SprintFailure } from '../domain/sprint-failure';
import { type Team } from '../domain/team';

/** Port double: get() answers the known teams, keeps 'slow' pending and refuses the rest. */
class FakeTeamsPort extends TeamsPort {
  readonly requested: string[] = [];
  readonly known: readonly Team[] = [
    aTeam('atlas', 'Atlas', 'admin'),
    aTeam('boreal', 'Boreal', 'admin'),
    aTeam('cielo', 'Cielo', 'member'),
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

function sprintOn(day: SprintDay): ActiveSprint {
  return {
    id: 'sprint-1',
    startDate: '2026-10-05',
    endDate: '2026-10-14',
    dailyTime: '2026-10-05T14:00:00Z',
    timeZone: 'America/Bogota',
    nextDailyAt: '2026-10-08T14:00:00Z',
    participants: ['ana'],
    day,
  };
}

/** Sprints port double: active() answers `answer` (the team has no sprint unless a test says so). */
class FakeSprintsPort extends SprintsPort {
  answer: Observable<ActiveSprint | null> = of(null);
  readonly read: string[] = [];

  active(teamId: string): Observable<ActiveSprint | null> {
    this.read.push(teamId);
    return this.answer;
  }

  start(): Observable<never> {
    return NEVER;
  }

  reconfigure(): Observable<never> {
    return NEVER;
  }
}

describe('TeamDashboardPage', () => {
  let port: FakeTeamsPort;
  let sprints: FakeSprintsPort;
  let harness: RouterTestingHarness;

  beforeEach(async () => {
    port = new FakeTeamsPort();
    sprints = new FakeSprintsPort();
    TestBed.configureTestingModule({
      providers: [
        provideTestI18n(),
        provideTestTenant(),
        provideRouter(
          [{ path: ':tenant/teams/:teamId', component: TeamDashboardPage }],
          withComponentInputBinding(),
        ),
        { provide: TeamsPort, useValue: port },
        { provide: SprintsPort, useValue: sprints },
        provideStubUsersPort(),
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
    const page = await open('/acme/teams/atlas');

    // The dashboard and the top bar each read the team: it is the same team, once per reader.
    expect(new Set(port.requested)).toEqual(new Set(['atlas']));
    expect(page.querySelector('h1')?.textContent.trim()).toBe('Atlas');
  });

  it('loads the other team when the :teamId changes', async () => {
    await open('/acme/teams/atlas');

    const page = await open('/acme/teams/boreal');

    expect([...new Set(port.requested)]).toEqual(['atlas', 'boreal']);
    expect(page.querySelector('h1')?.textContent.trim()).toBe('Boreal');
  });

  it('says it is loading while the API has not answered', async () => {
    // Not whenStable: the request stays pending, so the page never settles.
    await harness.navigateByUrl('/acme/teams/slow');
    TestBed.tick();
    const page = harness.routeNativeElement!;

    expect(page.textContent).toContain('Cargando el equipo…');
    expect(page.querySelector('h1')).toBeNull();
  });

  it('shows a translated message when the API refuses the team', async () => {
    const page = await open('/acme/teams/someone-elses');

    expect(page.querySelector('[role="alert"]')?.textContent).toBe('No se pudo abrir este equipo.');
    expect(page.querySelector('h1')).toBeNull();
  });

  it('shows an admin the way to the settings of the team', async () => {
    const page = await open('/acme/teams/atlas');

    const link = Array.from(page.querySelectorAll('a')).find(
      (candidate) => candidate.textContent.trim() === 'Configuración',
    );
    expect(link?.getAttribute('href')).toBe('/acme/teams/atlas/settings');
  });

  it('does not show a member the way to the settings: the API would refuse them', async () => {
    const page = await open('/acme/teams/cielo');

    expect(page.querySelector('h1')?.textContent.trim()).toBe('Cielo');
    expect(page.querySelector('a[href="/acme/teams/cielo/settings"]')).toBeNull();
    expect(page.textContent).not.toContain('Configuración');
  });

  // ----------------------------------------------------- criterion 6 (HU-07) --
  function sprintDay(page: HTMLElement): string | undefined {
    return page
      .querySelector('[data-testid="sprint-day"]')
      ?.textContent.replace(/\s+/g, ' ')
      .trim();
  }

  it('shows the day N of M of the sprint in progress, as the API computed it', async () => {
    sprints.answer = of(sprintOn({ number: 3, total: 10, phase: 'in_progress' }));

    const page = await open('/acme/teams/atlas');

    expect(sprints.read).toEqual(['atlas']);
    expect(sprintDay(page)).toBe('Día 3 de 10');
  });

  it('says when a sprint that has not started yet begins', async () => {
    sprints.answer = of(sprintOn({ number: 0, total: 10, phase: 'not_started' }));

    const page = await open('/acme/teams/atlas');

    expect(sprintDay(page)).toBe('El sprint empieza el 5 de octubre de 2026');
  });

  it('says the sprint is over once its last day has passed', async () => {
    sprints.answer = of(sprintOn({ number: 10, total: 10, phase: 'finished' }));

    const page = await open('/acme/teams/atlas');

    expect(sprintDay(page)).toBe('Sprint terminado');
  });

  it('says the team has no active sprint when the API answers none', async () => {
    const page = await open('/acme/teams/atlas');

    expect(sprintDay(page)).toBe('Sin sprint activo');
  });

  it('shows the day to a member too: reading the sprint is for everybody in the team', async () => {
    sprints.answer = of(sprintOn({ number: 1, total: 10, phase: 'in_progress' }));

    const page = await open('/acme/teams/cielo');

    expect(sprintDay(page)).toBe('Día 1 de 10');
  });

  it('leaves the line out, and still shows the team, when the sprint cannot be read', async () => {
    sprints.answer = throwError(() => new SprintFailure('unavailable'));

    const page = await open('/acme/teams/atlas');

    expect(page.querySelector('h1')?.textContent.trim()).toBe('Atlas');
    expect(sprintDay(page)).toBeUndefined();
    expect(page.textContent).not.toContain('Sin sprint activo');
    expect(page.querySelector('[role="alert"]')).toBeNull();
  });

  it('shows no line while the API has not answered about the sprint', async () => {
    sprints.answer = new Subject<ActiveSprint | null>();

    await harness.navigateByUrl('/acme/teams/atlas');
    TestBed.tick();
    const page = harness.routeNativeElement!;

    expect(page.querySelector('h1')?.textContent.trim()).toBe('Atlas');
    expect(sprintDay(page)).toBeUndefined();
  });

  it('reads the sprint of the other team when the :teamId changes', async () => {
    await open('/acme/teams/atlas');
    sprints.answer = of(sprintOn({ number: 2, total: 10, phase: 'in_progress' }));

    const page = await open('/acme/teams/boreal');

    expect(sprints.read).toEqual(['atlas', 'boreal']);
    expect(sprintDay(page)).toBe('Día 2 de 10');
  });
});
