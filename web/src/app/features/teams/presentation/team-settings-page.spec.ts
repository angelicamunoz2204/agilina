import { TestBed } from '@angular/core/testing';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { NEVER, of, Subject, throwError, type Observable } from 'rxjs';

import { provideTestI18n } from '@testing/i18n';

import { TeamSettingsPage } from './team-settings-page';
import { TeamMembersPort } from '../application/team-members.port';
import { MemberFailure } from '../domain/member-failure';
import {
  type InvitationOutcome,
  type MemberInvitation,
  type TeamMember,
  type TeamMembers,
  type TeamRole,
} from '../domain/team-member';

const ANA: TeamMember = {
  userId: 'ana',
  fullName: 'Ana Gil',
  email: 'ana@example.com',
  role: 'admin',
  label: 'admin',
  roleChangeBlockedBy: 'last_admin',
  removalBlockedBy: 'last_admin',
};
const BRUNO: TeamMember = {
  userId: 'bruno',
  fullName: 'Bruno Díaz',
  email: 'bruno@example.com',
  role: 'member',
  label: 'member',
  roleChangeBlockedBy: null,
  removalBlockedBy: null,
};

/**
 * Port double: list() answers what `answer` holds for the team (a failure, or nothing yet for
 * 'slow'); the commands wait until the test answers them.
 */
class FakeTeamMembersPort extends TeamMembersPort {
  answer: TeamMembers | MemberFailure = {
    roles: [
      { role: 'admin', label: 'admin' },
      { role: 'member', label: 'member' },
    ],
    members: [ANA, BRUNO],
  };
  readonly listed: string[] = [];
  readonly invitations: MemberInvitation[] = [];
  readonly changes: [string, TeamRole][] = [];
  readonly removals: string[] = [];
  private pendingCommand = new Subject<void>();
  private pendingInvitation = new Subject<InvitationOutcome>();

  list(teamId: string): Observable<TeamMembers> {
    this.listed.push(teamId);
    if (teamId === 'slow') {
      return NEVER;
    }
    const answer = this.answer;
    return answer instanceof MemberFailure ? throwError(() => answer) : of(answer);
  }

  invite(teamId: string, invitation: MemberInvitation): Observable<InvitationOutcome> {
    this.invitations.push(invitation);
    this.pendingInvitation = new Subject<InvitationOutcome>();
    return this.pendingInvitation;
  }

  changeRole(teamId: string, userId: string, role: TeamRole): Observable<void> {
    this.changes.push([userId, role]);
    return this.command();
  }

  remove(teamId: string, userId: string): Observable<void> {
    this.removals.push(userId);
    return this.command();
  }

  /** The API accepts the pending change. */
  accept(): void {
    this.pendingCommand.next();
    this.pendingCommand.complete();
  }

  /** The API refuses the pending change. */
  refuse(failure: Error): void {
    this.pendingCommand.error(failure);
  }

  /** The API answers the pending invitation. */
  answerInvitation(outcome: InvitationOutcome): void {
    this.pendingInvitation.next(outcome);
    this.pendingInvitation.complete();
  }

  private command(): Observable<void> {
    this.pendingCommand = new Subject<void>();
    return this.pendingCommand;
  }
}

describe('TeamSettingsPage', () => {
  let port: FakeTeamMembersPort;
  let harness: RouterTestingHarness;
  let page: HTMLElement;

  beforeEach(async () => {
    port = new FakeTeamMembersPort();
    TestBed.configureTestingModule({
      providers: [
        provideTestI18n(),
        provideRouter(
          [{ path: 'teams/:teamId/settings', component: TeamSettingsPage }],
          withComponentInputBinding(),
        ),
        { provide: TeamMembersPort, useValue: port },
      ],
    });
    harness = await RouterTestingHarness.create();
  });

  async function open(url = '/teams/atlas/settings'): Promise<void> {
    await harness.navigateByUrl(url);
    await harness.fixture.whenStable();
    page = harness.routeNativeElement!;
  }

  /** Lets the page react to an answer the facade awaited (see CreateTeamPage's spec). */
  async function settled(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve));
    await harness.fixture.whenStable();
  }

  function rows(): HTMLLIElement[] {
    return Array.from(page.querySelectorAll('li'));
  }

  function roleControl(userId: string): HTMLSelectElement {
    return page.querySelector<HTMLSelectElement>(`#member-role-${userId}`)!;
  }

  function button(text: string, scope: ParentNode = page): HTMLButtonElement {
    const found = Array.from(scope.querySelectorAll('button')).find(
      (candidate) => candidate.textContent.trim() === text,
    );
    expect(found).withContext(`a button "${text}"`).toBeDefined();
    return found!;
  }

  function removeButtonOf(name: string): HTMLButtonElement {
    return page.querySelector<HTMLButtonElement>(
      `button[aria-label="Eliminar a ${name} del equipo"]`,
    )!;
  }

  function dialog(): HTMLDialogElement | null {
    return page.querySelector('dialog');
  }

  function text(element: Element | null | undefined): string {
    return element?.textContent.replace(/\s+/g, ' ').trim() ?? '';
  }

  // ----------------------------------------------------------- criterion 1 --
  it('lists each member with name, email and the translated label of their role', async () => {
    await open();

    expect(port.listed).toEqual(['atlas']);
    expect(page.querySelector('h1')?.textContent).toBe('Equipo');
    const [ana, bruno] = rows();
    expect(text(ana)).toContain('Ana Gil');
    expect(text(ana)).toContain('ana@example.com');
    expect(text(ana)).toContain('Administrador');
    expect(text(bruno)).toContain('Bruno Díaz');
    expect(text(bruno)).toContain('bruno@example.com');
    expect(text(bruno)).toContain('Miembro');
  });

  it('shows each role in a control with the options the API gave', async () => {
    await open();

    const control = roleControl('bruno');
    expect(control.value).toBe('member');
    expect(Array.from(control.options).map((option) => option.text.trim())).toEqual([
      'Administrador',
      'Miembro',
    ]);
    expect(page.querySelector('label[for="member-role-bruno"]')?.textContent.trim()).toBe(
      'Rol de Bruno Díaz',
    );
  });

  it('says it is loading while the API has not answered', async () => {
    await harness.navigateByUrl('/teams/slow/settings');
    TestBed.tick();
    page = harness.routeNativeElement!;

    expect(text(page.querySelector('[role="status"]'))).toBe('Cargando a los integrantes…');
    expect(rows()).toEqual([]);
  });

  // ----------------------------------------------------------- criterion 3 --
  it('disables the role of a member with the reason the API gives, tied to the control', async () => {
    port.answer = {
      roles: [
        { role: 'admin', label: 'admin' },
        { role: 'member', label: 'member' },
      ],
      members: [
        { ...ANA, roleChangeBlockedBy: 'sprint_in_progress' },
        { ...BRUNO, roleChangeBlockedBy: 'sprint_in_progress' },
      ],
    };
    await open();

    const control = roleControl('bruno');
    expect(control.disabled).toBeTrue();
    const reason = page.querySelector(`#${control.getAttribute('aria-describedby')!}`);
    expect(text(reason)).toBe(
      'No se puede cambiar el rol mientras el equipo tiene un sprint activo.',
    );
  });

  it('leaves the role of a member enabled, without a reason, when nothing blocks it', async () => {
    await open();

    expect(roleControl('bruno').disabled).toBeFalse();
    expect(roleControl('bruno').hasAttribute('aria-describedby')).toBeFalse();
    expect(roleControl('ana').disabled).toBeTrue();
    expect(text(page.querySelector('#member-role-blocked-ana'))).toBe(
      'Es el único Administrador: el equipo no puede quedarse sin Administrador.',
    );
  });

  it('changes the role of a member and asks the API for the list again', async () => {
    await open();

    roleControl('bruno').value = 'admin';
    roleControl('bruno').dispatchEvent(new Event('change'));
    await harness.fixture.whenStable();
    expect(text(page.querySelector('[role="status"]'))).toBe('Guardando…');
    expect(roleControl('bruno').disabled).toBeTrue();
    port.accept();
    await settled();

    expect(port.changes).toEqual([['bruno', 'admin']]);
    expect(port.listed).toEqual(['atlas', 'atlas']);
    expect(page.querySelector('[role="alert"]')).toBeNull();
  });

  it('puts the role back and says why when the API refuses the change', async () => {
    await open();

    roleControl('bruno').value = 'admin';
    roleControl('bruno').dispatchEvent(new Event('change'));
    port.refuse(new MemberFailure('sprint_in_progress'));
    await settled();

    expect(roleControl('bruno').value).toBe('member');
    expect(text(page.querySelector('[role="alert"]'))).toBe(
      'No se puede cambiar el rol mientras el equipo tiene un sprint activo.',
    );
    expect(port.listed).toEqual(['atlas', 'atlas']);
  });

  // ----------------------------------------------------------- criterion 4 --
  it('asks for confirmation before removing, warning about the calls of the team', async () => {
    await open();

    removeButtonOf('Bruno Díaz').click();
    await harness.fixture.whenStable();

    const confirmation = dialog();
    expect(confirmation?.open).toBeTrue();
    expect(text(confirmation?.querySelector('h2'))).toBe('¿Eliminar a Bruno Díaz del equipo?');
    expect(text(confirmation)).toContain(
      'Bruno Díaz dejará de pertenecer al equipo y de recibir sus convocatorias.',
    );
    expect(text(confirmation)).toContain('Su cuenta de Agilina no se borra');
    expect(port.removals).toEqual([]);
  });

  it('removes the member once confirmed and closes the confirmation', async () => {
    await open();
    removeButtonOf('Bruno Díaz').click();
    await harness.fixture.whenStable();

    button('Eliminar del equipo', dialog()!).click();
    port.answer = { roles: [], members: [ANA] };
    port.accept();
    await settled();

    expect(port.removals).toEqual(['bruno']);
    expect(dialog()).toBeNull();
    expect(rows().map((row) => text(row))).not.toContain(jasmine.stringContaining('Bruno'));
  });

  it('does not remove anybody when the confirmation is cancelled', async () => {
    await open();
    removeButtonOf('Bruno Díaz').click();
    await harness.fixture.whenStable();

    button('Cancelar', dialog()!).click();
    await harness.fixture.whenStable();

    expect(dialog()).toBeNull();
    expect(port.removals).toEqual([]);
  });

  it('keeps the confirmation open and says why when the API refuses the removal', async () => {
    await open();
    removeButtonOf('Bruno Díaz').click();
    await harness.fixture.whenStable();

    button('Eliminar del equipo', dialog()!).click();
    port.refuse(new MemberFailure('not_found'));
    await settled();

    expect(dialog()?.open).toBeTrue();
    expect(text(dialog()?.querySelector('[role="alert"]'))).toBe(
      'Esta persona ya no está en el equipo.',
    );
  });

  // ----------------------------------------------------------- criterion 5 --
  it('does not let the only admin be removed and says why', async () => {
    await open();

    const remove = removeButtonOf('Ana Gil');
    expect(remove.disabled).toBeTrue();
    expect(text(page.querySelector(`#${remove.getAttribute('aria-describedby')!}`))).toBe(
      'Es el único Administrador: no se puede eliminar del equipo.',
    );
    expect(removeButtonOf('Bruno Díaz').disabled).toBeFalse();
  });

  // ----------------------------------------------------------- criterion 2 --
  it('invites a member and tells what the API did', async () => {
    await open();

    button('Invitar miembro').click();
    await harness.fixture.whenStable();
    const form = dialog()!;
    const name = form.querySelector<HTMLInputElement>('#invite-full-name')!;
    const email = form.querySelector<HTMLInputElement>('#invite-email')!;
    name.value = 'Laura';
    name.dispatchEvent(new Event('input'));
    email.value = 'laura@example.com';
    email.dispatchEvent(new Event('input'));
    await harness.fixture.whenStable();
    button('Enviar invitación', form).click();
    port.answerInvitation('invitation_sent');
    await settled();

    expect(port.invitations).toEqual([
      { fullName: 'Laura', email: 'laura@example.com', role: 'member' },
    ]);
    expect(dialog()).toBeNull();
    expect(text(page.querySelector('[role="status"]'))).toBe(
      'Enviamos la invitación por correo. El enlace de activación vale 7 días.',
    );
    expect(port.listed).toEqual(['atlas', 'atlas']);
  });

  // ----------------------------------------------------------- criterion 6 --
  it('shows "no access" when the API refuses the screen to this user', async () => {
    port.answer = new MemberFailure('forbidden');
    await open();

    expect(page.querySelector('h1')?.textContent).toBe('No tienes acceso a esta pantalla');
    expect(text(page)).toContain(
      'Solo los Administradores del equipo pueden gestionar a sus integrantes.',
    );
    expect(rows()).toEqual([]);
    expect(page.querySelector('select')).toBeNull();
    expect(page.querySelector('a[href="/teams/atlas"]')).not.toBeNull();
  });

  it('asks to sign in again when the API does not recognise the session', async () => {
    port.answer = new MemberFailure('not_authenticated');
    await open();

    expect(text(page.querySelector('[role="alert"]'))).toBe(
      'Tu sesión no es válida o expiró. Inicia sesión de nuevo.',
    );
    expect(rows()).toEqual([]);
  });

  it('shows a generic message when the list cannot be loaded for another reason', async () => {
    port.answer = new MemberFailure('unavailable');
    await open();

    expect(text(page.querySelector('[role="alert"]'))).toBe(
      'No se pudo cargar a los integrantes. Inténtalo de nuevo más tarde.',
    );
    expect(page.querySelector('h1')?.textContent).toBe('Equipo');
  });
});
