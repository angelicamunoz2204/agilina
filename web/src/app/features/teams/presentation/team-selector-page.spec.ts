import { TestBed } from '@angular/core/testing';
import { provideRouter, Router, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { NEVER, of, Subject, throwError, type Observable } from 'rxjs';

import { provideTestI18n } from '@testing/i18n';
import { provideTestTenant } from '@testing/tenant';

import { CreateTeamPage } from './create-team-page';
import { TeamDashboardPage } from './team-dashboard-page';
import { TeamSelectorPage } from './team-selector-page';
import { TeamsPort } from '../application/teams.port';
import { type Team } from '../domain/team';

/** Port double: listMine() answers what the test chose; get() finds the team by id. */
class FakeTeamsPort extends TeamsPort {
  mine: Observable<readonly Team[]> = of([]);
  known: readonly Team[] = [];

  listMine(): Observable<readonly Team[]> {
    return this.mine;
  }

  create(): Observable<string> {
    return NEVER;
  }

  get(teamId: string): Observable<Team> {
    const team = this.known.find((candidate) => candidate.id === teamId);
    return team === undefined ? throwError(() => new Error('403')) : of(team);
  }
}

describe('TeamSelectorPage', () => {
  let port: FakeTeamsPort;
  let harness: RouterTestingHarness;

  beforeEach(async () => {
    port = new FakeTeamsPort();
    TestBed.configureTestingModule({
      providers: [
        provideTestI18n(),
        provideTestTenant(),
        provideRouter(
          [
            { path: ':tenant/teams', component: TeamSelectorPage },
            { path: ':tenant/teams/new', component: CreateTeamPage },
            { path: ':tenant/teams/:teamId', component: TeamDashboardPage },
          ],
          withComponentInputBinding(),
        ),
        { provide: TeamsPort, useValue: port },
      ],
    });
    harness = await RouterTestingHarness.create();
  });

  async function open(teams: Observable<readonly Team[]>): Promise<HTMLElement> {
    port.mine = teams;
    await harness.navigateByUrl('/acme/teams');
    await harness.fixture.whenStable();
    return harness.routeNativeElement!;
  }

  function links(page: HTMLElement): { text: string; href: string | null }[] {
    return Array.from(page.querySelectorAll('ul a')).map((link) => ({
      text: link.textContent.trim(),
      href: link.getAttribute('href'),
    }));
  }

  it('shows the name of each team of the user with a link to its dashboard', async () => {
    const page = await open(
      of([
        { id: 'a', name: 'Atlas' },
        { id: 'b', name: 'Boreal' },
      ]),
    );

    expect(page.querySelector('h1')?.textContent).toBe('Selecciona tu equipo');
    expect(links(page)).toEqual([
      { text: 'Atlas', href: '/acme/teams/a' },
      { text: 'Boreal', href: '/acme/teams/b' },
    ]);
    expect(page.textContent).not.toContain('Todavía no perteneces');
  });

  it('enters the dashboard of the team the user clicks', async () => {
    port.known = [{ id: 'b', name: 'Boreal' }];
    const page = await open(
      of([
        { id: 'a', name: 'Atlas' },
        { id: 'b', name: 'Boreal' },
      ]),
    );

    page.querySelectorAll<HTMLAnchorElement>('ul a')[1]!.click();
    await harness.fixture.whenStable();

    expect(TestBed.inject(Router).url).toBe('/acme/teams/b');
    expect(harness.routeNativeElement?.querySelector('h1')?.textContent.trim()).toBe('Boreal');
  });

  it('with no team shows the empty list and the button to create one', async () => {
    const page = await open(of([]));

    expect(links(page)).toEqual([]);
    expect(page.textContent).toContain('Todavía no perteneces a ningún equipo.');
    const create = page.querySelector('a[href="/acme/teams/new"]');
    expect(create?.textContent.trim()).toBe('Crear equipo nuevo');
    expect(create?.getAttribute('href')).toBe('/acme/teams/new');
  });

  it('goes straight into the only team: there is nothing to choose', async () => {
    port.known = [{ id: 'a', name: 'Atlas' }];

    await open(of([{ id: 'a', name: 'Atlas' }]));

    expect(TestBed.inject(Router).url).toBe('/acme/teams/a');
    expect(harness.routeNativeElement?.querySelector('h1')?.textContent.trim()).toBe('Atlas');
  });

  it('always offers to create a team', async () => {
    const page = await open(
      of([
        { id: 'a', name: 'Atlas' },
        { id: 'b', name: 'Boreal' },
      ]),
    );

    expect(page.querySelector('a[href="/acme/teams/new"]')?.getAttribute('href')).toBe(
      '/acme/teams/new',
    );
  });

  it('takes the user to the creation form', async () => {
    const page = await open(of([]));

    page.querySelector<HTMLAnchorElement>('a[href="/acme/teams/new"]')!.click();
    await harness.fixture.whenStable();

    expect(TestBed.inject(Router).url).toBe('/acme/teams/new');
    expect(harness.routeNativeElement?.querySelector('form')).not.toBeNull();
  });

  it('does not show the role of the user in each team', async () => {
    const page = await open(
      of([
        { id: 'a', name: 'Atlas' },
        { id: 'b', name: 'Boreal' },
      ]),
    );

    expect(page.textContent).not.toMatch(/admin|member|miembro/i);
  });

  it('says it is loading while the API has not answered', async () => {
    port.mine = new Subject<readonly Team[]>();
    // Not whenStable: the request stays pending, so the page never settles.
    await harness.navigateByUrl('/acme/teams');
    TestBed.tick();
    const page = harness.routeNativeElement!;

    expect(page.textContent).toContain('Cargando tus equipos…');
    expect(links(page)).toEqual([]);
  });

  it('shows a translated message when the teams cannot be loaded', async () => {
    const page = await open(throwError(() => new Error('503')));

    expect(page.querySelector('[role="alert"]')?.textContent).toBe(
      'No se pudieron cargar tus equipos. Inténtalo de nuevo más tarde.',
    );
    expect(page.querySelector('a[href="/acme/teams/new"]')?.getAttribute('href')).toBe(
      '/acme/teams/new',
    );
  });
});
