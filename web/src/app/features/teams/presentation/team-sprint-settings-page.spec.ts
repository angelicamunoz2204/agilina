import { TestBed } from '@angular/core/testing';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { NEVER, of, Subject, throwError, type Observable } from 'rxjs';

import { BROWSER_TIME_ZONE } from '@core/time/browser-time-zone';
import { formatLocalDateTime } from '@shared/utils/local-date-time';
import { provideTestI18n } from '@testing/i18n';
import { provideTestTenant } from '@testing/tenant';

import { TeamSprintSettingsPage } from './team-sprint-settings-page';
import { SprintsPort } from '../application/sprints.port';
import { TeamMembersPort } from '../application/team-members.port';
import { type ActiveSprint } from '../domain/active-sprint';
import { MemberFailure } from '../domain/member-failure';
import { type SprintDraft } from '../domain/sprint-draft';
import { SprintFailure } from '../domain/sprint-failure';
import { type TeamMember, type TeamMembers } from '../domain/team-member';

function member(userId: string, fullName: string): TeamMember {
  return {
    userId,
    fullName,
    email: `${userId}@example.com`,
    role: 'member',
    label: 'member',
    roleChangeBlockedBy: null,
    removalBlockedBy: null,
  };
}

const ANA = member('ana', 'Ana Gil');
const BRUNO = member('bruno', 'Bruno Díaz');
const CARLA = member('carla', 'Carla Ruiz');

/*
 * The instants are built from wall-clock times in the zone of whoever runs the tests, so the
 * time the page shows is the same on any machine: the page always works in the browser's zone.
 */
const SPRINT: ActiveSprint = {
  id: 'sprint-1',
  startDate: '2026-10-05',
  endDate: '2026-10-16',
  dailyTime: new Date(2026, 9, 5, 9, 0).toISOString(),
  timeZone: 'America/Bogota',
  nextDailyAt: new Date(2026, 9, 8, 9, 0).toISOString(),
  participants: ['bruno', 'ana'],
  day: { number: 3, total: 12, phase: 'in_progress' },
};

/**
 * Sprints port double: active() answers what `current` holds (nothing yet for the team 'slow');
 * start() and reconfigure() wait until the test answers them.
 */
class FakeSprintsPort extends SprintsPort {
  current: ActiveSprint | null | SprintFailure = SPRINT;
  readonly read: string[] = [];
  readonly started: SprintDraft[] = [];
  readonly reconfigured: SprintDraft[] = [];
  private pending = new Subject<ActiveSprint>();

  active(teamId: string): Observable<ActiveSprint | null> {
    this.read.push(teamId);
    if (teamId === 'slow') {
      return NEVER;
    }
    const current = this.current;
    return current instanceof SprintFailure ? throwError(() => current) : of(current);
  }

  start(teamId: string, draft: SprintDraft): Observable<ActiveSprint> {
    this.started.push(draft);
    return this.command();
  }

  reconfigure(teamId: string, draft: SprintDraft): Observable<ActiveSprint> {
    this.reconfigured.push(draft);
    return this.command();
  }

  /** The API saves the sprint and answers it. */
  accept(sprint: ActiveSprint): void {
    this.pending.next(sprint);
    this.pending.complete();
  }

  /** The API refuses the save. */
  refuse(failure: Error): void {
    this.pending.error(failure);
  }

  private command(): Observable<ActiveSprint> {
    this.pending = new Subject<ActiveSprint>();
    return this.pending;
  }
}

/** Members port double: list() answers `answer`; the sprint screen uses nothing else. */
class FakeTeamMembersPort extends TeamMembersPort {
  answer: TeamMembers | MemberFailure = { roles: [], members: [ANA, BRUNO, CARLA] };

  list(): Observable<TeamMembers> {
    const answer = this.answer;
    return answer instanceof MemberFailure ? throwError(() => answer) : of(answer);
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

describe('TeamSprintSettingsPage', () => {
  let sprints: FakeSprintsPort;
  let members: FakeTeamMembersPort;
  let harness: RouterTestingHarness;
  let page: HTMLElement;

  beforeEach(async () => {
    sprints = new FakeSprintsPort();
    members = new FakeTeamMembersPort();
    TestBed.configureTestingModule({
      providers: [
        provideTestI18n(),
        provideTestTenant(),
        provideRouter(
          [{ path: ':tenant/teams/:teamId/settings/sprint', component: TeamSprintSettingsPage }],
          withComponentInputBinding(),
        ),
        { provide: SprintsPort, useValue: sprints },
        { provide: TeamMembersPort, useValue: members },
        // The browser of whoever opens the screen, fixed: not the zone of the machine.
        { provide: BROWSER_TIME_ZONE, useValue: 'America/Bogota' },
      ],
    });
    harness = await RouterTestingHarness.create();
  });

  async function open(url = '/acme/teams/atlas/settings/sprint'): Promise<void> {
    await harness.navigateByUrl(url);
    await harness.fixture.whenStable();
    page = harness.routeNativeElement!;
  }

  /** Lets the page react to an answer the facade awaited (see CreateTeamPage's spec). */
  async function settled(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve));
    await harness.fixture.whenStable();
  }

  function text(element: Element | null | undefined): string {
    return element?.textContent.replace(/\s+/g, ' ').trim() ?? '';
  }

  /** The control a `<label for>` with this text names. */
  function field(label: string): HTMLInputElement {
    const found = Array.from(page.querySelectorAll('label[for]')).find(
      (candidate) => text(candidate) === label,
    );
    expect(found).withContext(`a label "${label}"`).toBeDefined();
    return page.querySelector<HTMLInputElement>(`#${found!.getAttribute('for')!}`)!;
  }

  async function type(control: HTMLInputElement, value: string): Promise<void> {
    control.value = value;
    control.dispatchEvent(new Event('input'));
    await harness.fixture.whenStable();
  }

  /** The checkbox of a member among the daily's participants. */
  function checkbox(name: string): HTMLInputElement {
    const found = Array.from(page.querySelectorAll('fieldset label')).find(
      (candidate) => text(candidate) === name,
    );
    expect(found).withContext(`a participant "${name}"`).toBeDefined();
    return found!.querySelector('input[type="checkbox"]')!;
  }

  async function toggle(name: string): Promise<void> {
    checkbox(name).click();
    await harness.fixture.whenStable();
  }

  /** The names in the turn order, first speaker first, with their position. */
  function turns(): string[] {
    return Array.from(page.querySelectorAll('ol li')).map((row) => text(row));
  }

  function moveButton(direction: 'Subir' | 'Bajar', name: string): HTMLButtonElement {
    return page.querySelector<HTMLButtonElement>(`button[aria-label="${direction} a ${name}"]`)!;
  }

  /** What the live regions announce to a screen reader. */
  function announcements(): string[] {
    return Array.from(page.querySelectorAll('[aria-live="polite"]')).map((region) => text(region));
  }

  function submitButton(): HTMLButtonElement {
    return page.querySelector<HTMLButtonElement>('button[type="submit"]')!;
  }

  async function submit(): Promise<void> {
    submitButton().click();
    await harness.fixture.whenStable();
  }

  // --------------------------------------------------------------- the screen --
  it('is the Sprint tab of the settings, with the active sprint marked and no name', async () => {
    await open();

    expect(sprints.read).toEqual(['atlas']);
    expect(text(page.querySelector('h1'))).toBe('Configuración');
    expect(text(page.querySelector('nav a[aria-current="page"]'))).toBe('Sprint');
    expect(text(page.querySelector('h2'))).toBe('Sprint');
    expect(text(page)).toContain('Sprint activo');
    expect(text(page)).not.toContain('Sprint 1');
    expect(page.querySelector('a[href="/acme/teams/atlas"]')).not.toBeNull();
  });

  it('configures only the daily: no retro, no review and no way to close the sprint', async () => {
    await open();

    expect(text(page)).not.toMatch(/retro|review|cerrar/i);
  });

  it('does not mark the sprint as active while the team has none, and starts empty', async () => {
    sprints.current = null;
    await open();

    expect(text(page)).not.toContain('Sprint activo');
    expect(field('Inicio').value).toBe('');
    expect(field('Fin').value).toBe('');
    expect(field('Hora de la daily (única para el equipo)').value).toBe('');
    expect(checkbox('Ana Gil').checked).toBeFalse();
    expect(turns()).toEqual([]);
    expect(text(page)).toContain('Marca a los participantes de la daily para ordenar sus turnos.');
    expect(submitButton().disabled).toBeTrue();
  });

  it('says it is loading while the API has not answered', async () => {
    await harness.navigateByUrl('/acme/teams/slow/settings/sprint');
    TestBed.tick();
    page = harness.routeNativeElement!;

    expect(text(page.querySelector('[role="status"]'))).toBe('Cargando el sprint…');
    expect(page.querySelector('form')).toBeNull();
  });

  // ------------------------------------------------- criteria 1, 2 and 3b ------
  it('fills the form with the saved dates and the daily time in the browser zone', async () => {
    await open();

    expect(field('Inicio').type).toBe('date');
    expect(field('Inicio').value).toBe('2026-10-05');
    expect(field('Fin').value).toBe('2026-10-16');
    const time = field('Hora de la daily (única para el equipo)');
    expect(time.type).toBe('time');
    expect(time.value).toBe('09:00');
  });

  it('shows the time of the anchor when no daily is left in the sprint', async () => {
    sprints.current = {
      ...SPRINT,
      dailyTime: new Date(2026, 9, 5, 8, 15).toISOString(),
      nextDailyAt: null,
      day: { number: 12, total: 12, phase: 'finished' },
    };
    await open();

    expect(field('Hora de la daily (única para el equipo)').value).toBe('08:15');
    expect(text(page)).toContain('Ya no quedan dailies en este sprint.');
  });

  it('says the times are in the browser zone and shows the next daily in it', async () => {
    await open();

    expect(text(page)).toContain(
      'Las horas se muestran en la zona horaria de tu navegador (America/Bogota).',
    );
    expect(text(page)).toContain('La hora de la daily está guardada en la zona America/Bogota.');
    expect(text(page)).toContain(
      `Próxima daily: ${formatLocalDateTime(SPRINT.nextDailyAt!, 'es')}.`,
    );
    expect(text(page)).not.toContain('pasará a la zona de tu navegador');
  });

  it('warns that saving moves the daily to the browser zone when it was saved in another', async () => {
    sprints.current = { ...SPRINT, timeZone: 'Europe/Madrid' };
    await open();

    expect(text(page)).toContain('La hora de la daily está guardada en la zona Europe/Madrid.');
    expect(text(page)).toContain(
      'Al guardar, la hora de la daily pasará a la zona de tu navegador.',
    );
  });

  it('ties the zone of the browser to the time control', async () => {
    await open();

    const described = field('Hora de la daily (única para el equipo)')
      .getAttribute('aria-describedby')!
      .split(' ')
      .map((id) => text(page.querySelector(`#${id}`)));
    expect(described).toContain(
      'Las horas se muestran en la zona horaria de tu navegador (America/Bogota).',
    );
  });

  it('does not accept an end before the start, and says why', async () => {
    await open();

    await type(field('Fin'), '2026-10-01');

    expect(field('Fin').getAttribute('aria-invalid')).toBe('true');
    expect(text(page)).toContain('La fecha de fin no puede ser anterior a la de inicio.');
    expect(submitButton().disabled).toBeTrue();
  });

  it('accepts an end on the same day as the start', async () => {
    await open();

    await type(field('Fin'), '2026-10-05');

    expect(field('Fin').getAttribute('aria-invalid')).toBe('false');
    expect(submitButton().disabled).toBeFalse();
  });

  it('asks for a date and the time once the person leaves them empty', async () => {
    await open();

    await type(field('Inicio'), '');
    await type(field('Hora de la daily (única para el equipo)'), '');

    expect(text(page)).toContain('Elige la fecha de inicio.');
    expect(text(page)).toContain('Elige la hora de la daily.');
    expect(submitButton().disabled).toBeTrue();
  });

  it('asks for the end date once the person leaves it, not before', async () => {
    sprints.current = null;
    await open();
    expect(text(page)).not.toContain('Elige la fecha de fin.');

    field('Fin').dispatchEvent(new Event('blur'));
    await harness.fixture.whenStable();

    expect(text(page)).toContain('Elige la fecha de fin.');
  });

  // ----------------------------------------------------------- criterion 3 --
  it('offers every member of the team as a participant and checks the saved ones', async () => {
    await open();

    expect(text(page.querySelector('legend'))).toBe('Participantes de la daily');
    expect(checkbox('Ana Gil').checked).toBeTrue();
    expect(checkbox('Bruno Díaz').checked).toBeTrue();
    expect(checkbox('Carla Ruiz').checked).toBeFalse();
  });

  it('adds a checked member at the end of the turns and takes an unchecked one out', async () => {
    await open();

    await toggle('Carla Ruiz');
    expect(turns()).toEqual(['1 Bruno Díaz', '2 Ana Gil', '3 Carla Ruiz']);

    await toggle('Bruno Díaz');
    expect(checkbox('Bruno Díaz').checked).toBeFalse();
    expect(turns()).toEqual(['1 Ana Gil', '2 Carla Ruiz']);
  });

  it('asks for at least one participant once the last one is unchecked', async () => {
    await open();

    await toggle('Ana Gil');
    await toggle('Bruno Díaz');

    expect(turns()).toEqual([]);
    expect(text(page)).toContain('Elige al menos un participante para la daily.');
    expect(submitButton().disabled).toBeTrue();
  });

  it('leaves out of the turns a saved participant who is no longer a member', async () => {
    sprints.current = { ...SPRINT, participants: ['bruno', 'gone', 'ana'] };
    await open();

    expect(turns()).toEqual(['1 Bruno Díaz', '2 Ana Gil']);
  });

  // ----------------------------------------------------------- criterion 4 --
  it('shows the saved participants in their turn order, numbered', async () => {
    await open();

    expect(text(page)).toContain('Orden de turnos de la daily');
    expect(turns()).toEqual(['1 Bruno Díaz', '2 Ana Gil']);
  });

  it('moves a participant up and down, and announces the new turn', async () => {
    await open();
    await toggle('Carla Ruiz');

    moveButton('Subir', 'Carla Ruiz').click();
    await harness.fixture.whenStable();
    expect(turns()).toEqual(['1 Bruno Díaz', '2 Carla Ruiz', '3 Ana Gil']);
    expect(announcements()).toContain('Carla Ruiz ahora tiene el turno 2.');

    moveButton('Bajar', 'Bruno Díaz').click();
    await harness.fixture.whenStable();
    expect(turns()).toEqual(['1 Carla Ruiz', '2 Bruno Díaz', '3 Ana Gil']);
    expect(announcements()).toContain('Bruno Díaz ahora tiene el turno 2.');
  });

  it('cannot move the first one up nor the last one down', async () => {
    await open();
    await toggle('Carla Ruiz');

    expect(moveButton('Subir', 'Bruno Díaz').disabled).toBeTrue();
    expect(moveButton('Bajar', 'Bruno Díaz').disabled).toBeFalse();
    expect(moveButton('Subir', 'Ana Gil').disabled).toBeFalse();
    expect(moveButton('Bajar', 'Ana Gil').disabled).toBeFalse();
    expect(moveButton('Subir', 'Carla Ruiz').disabled).toBeFalse();
    expect(moveButton('Bajar', 'Carla Ruiz').disabled).toBeTrue();
  });

  // ------------------------------------------------------- saving (CA1–CA5) --
  it('creates the sprint when the team has none, with the daily in UTC and the browser zone', async () => {
    sprints.current = null;
    await open();

    await type(field('Inicio'), '2026-10-19');
    await type(field('Fin'), '2026-10-30');
    await type(field('Hora de la daily (única para el equipo)'), '09:30');
    await toggle('Carla Ruiz');
    await toggle('Ana Gil');
    await submit();

    expect(sprints.reconfigured).toEqual([]);
    expect(sprints.started).toEqual([
      {
        startDate: '2026-10-19',
        endDate: '2026-10-30',
        dailyTime: new Date(2026, 9, 19, 9, 30).toISOString(),
        timeZone: 'America/Bogota',
        participants: ['carla', 'ana'],
      },
    ]);
    expect(sprints.started[0]?.dailyTime).toMatch(/Z$/);

    sprints.accept({
      ...SPRINT,
      id: 'sprint-2',
      startDate: '2026-10-19',
      endDate: '2026-10-30',
      participants: ['carla', 'ana'],
    });
    await settled();

    expect(text(page.querySelector('[role="status"]'))).toBe('Sprint guardado.');
    expect(text(page)).toContain('Sprint activo');
    expect(turns()).toEqual(['1 Carla Ruiz', '2 Ana Gil']);
    expect(page.querySelector('[role="alert"]')).toBeNull();
  });

  it('edits the active sprint with the new order of the turns', async () => {
    await open();

    moveButton('Subir', 'Ana Gil').click();
    await harness.fixture.whenStable();
    await submit();

    expect(sprints.started).toEqual([]);
    expect(sprints.reconfigured).toEqual([
      {
        startDate: '2026-10-05',
        endDate: '2026-10-16',
        dailyTime: new Date(2026, 9, 5, 9, 0).toISOString(),
        timeZone: 'America/Bogota',
        participants: ['ana', 'bruno'],
      },
    ]);
  });

  it('is saving meanwhile: it cannot be sent again nor the turns moved', async () => {
    await open();

    await submit();

    expect(text(submitButton())).toBe('Guardando…');
    expect(submitButton().disabled).toBeTrue();
    expect(moveButton('Bajar', 'Bruno Díaz').disabled).toBeTrue();
    await submit();
    expect(sprints.reconfigured.length).toBe(1);

    sprints.accept(SPRINT);
    await settled();
    expect(text(submitButton())).toBe('Guardar sprint');
    expect(submitButton().disabled).toBeFalse();
  });

  it('stops saying it saved once something changes', async () => {
    await open();
    await submit();
    sprints.accept(SPRINT);
    await settled();
    expect(text(page)).toContain('Sprint guardado.');

    await toggle('Carla Ruiz');

    expect(text(page)).not.toContain('Sprint guardado.');
  });

  const refusals: [string, string][] = [
    ['ends_before_start', 'La fecha de fin no puede ser anterior a la de inicio.'],
    [
      'invalid_time_zone',
      'La zona horaria de tu navegador no es una zona válida. Revisa la configuración de tu dispositivo.',
    ],
    ['no_participants', 'Elige al menos un participante para la daily.'],
    ['duplicate_participant', 'Un participante aparece más de una vez.'],
    [
      'participant_not_a_member',
      'Uno de los participantes ya no es integrante del equipo. Recarga la página y vuelve a elegirlos.',
    ],
    [
      'active_sprint_exists',
      'Alguien más configuró el sprint del equipo mientras tanto. Revisa los datos y guarda de nuevo.',
    ],
    [
      'no_active_sprint',
      'El equipo ya no tiene un sprint activo. Revisa los datos y guarda de nuevo.',
    ],
    ['not_authenticated', 'Tu sesión no es válida o expiró. Inicia sesión de nuevo.'],
    ['unavailable', 'No se pudo guardar el sprint. Inténtalo de nuevo.'],
  ];

  refusals.forEach(([kind, message]) => {
    it(`says why the API refused the sprint (${kind}), as an alert`, async () => {
      await open();

      await submit();
      sprints.refuse(new SprintFailure(kind as SprintFailure['kind']));
      await settled();

      expect(text(page.querySelector('[role="alert"]'))).toBe(message);
      expect(text(page)).not.toContain('Sprint guardado.');
      expect(page.querySelector('form')).not.toBeNull();
    });
  });

  // ------------------------------------------------------------- no access --
  it('shows "no access" when the API refuses the screen to this user', async () => {
    members.answer = new MemberFailure('forbidden');
    await open();

    expect(text(page.querySelector('[data-testid="settings-forbidden-title"]'))).toBe(
      'No tienes acceso a esta pantalla',
    );
    expect(text(page)).toContain(
      'Solo los Administradores del equipo pueden configurar el sprint.',
    );
    expect(page.querySelector('form')).toBeNull();
    expect(page.querySelector('nav')).toBeNull();
    expect(page.querySelector('a[href="/acme/teams/atlas"]')).not.toBeNull();
  });

  it('shows "no access" when the API refuses the sprint itself', async () => {
    sprints.current = new SprintFailure('forbidden');
    await open();

    expect(page.querySelector('[data-testid="settings-forbidden-title"]')).not.toBeNull();
    expect(page.querySelector('form')).toBeNull();
  });

  it('shows "no access" when the API refuses the save: the admin lost the role meanwhile', async () => {
    await open();

    await submit();
    sprints.refuse(new SprintFailure('forbidden'));
    await settled();

    expect(page.querySelector('[data-testid="settings-forbidden-title"]')).not.toBeNull();
    expect(page.querySelector('form')).toBeNull();
  });

  it('asks to sign in again when the API does not recognise the session', async () => {
    sprints.current = new SprintFailure('not_authenticated');
    await open();

    expect(text(page.querySelector('[role="alert"]'))).toBe(
      'Tu sesión no es válida o expiró. Inicia sesión de nuevo.',
    );
    expect(page.querySelector('form')).toBeNull();
  });

  it('shows a generic message when the screen cannot be loaded for another reason', async () => {
    members.answer = new MemberFailure('unavailable');
    await open();

    expect(text(page.querySelector('[role="alert"]'))).toBe(
      'No se pudo cargar el sprint. Inténtalo de nuevo más tarde.',
    );
    expect(page.querySelector('form')).toBeNull();
  });
});
