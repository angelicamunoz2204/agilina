import { Component, signal } from '@angular/core';
import { TestBed, type ComponentFixture } from '@angular/core/testing';
import { NEVER, Subject, type Observable } from 'rxjs';

import { provideTestI18n } from '@testing/i18n';

import { InviteMemberDialog } from './invite-member-dialog';
import { UsersPort } from '../application/users.port';
import { MemberFailure } from '../domain/member-failure';
import {
  type InvitationOutcome,
  type MemberInvitation,
  type RoleOption,
} from '../domain/team-member';

/** Port double: each invite() waits until the test answers it. */
class FakeUsersPort extends UsersPort {
  readonly invitations: [string, MemberInvitation][] = [];
  pending = new Subject<InvitationOutcome>();

  list(): Observable<never> {
    return NEVER;
  }

  get(): Observable<never> {
    return NEVER;
  }

  me(): Observable<never> {
    return NEVER;
  }

  invite(teamId: string, invitation: MemberInvitation): Observable<InvitationOutcome> {
    this.invitations.push([teamId, invitation]);
    this.pending = new Subject<InvitationOutcome>();
    return this.pending;
  }

  changeRole(): Observable<never> {
    return NEVER;
  }

  remove(): Observable<never> {
    return NEVER;
  }
}

@Component({
  imports: [InviteMemberDialog],
  template: `
    @if (open()) {
      <agl-invite-member-dialog
        teamId="atlas"
        [roles]="roles"
        (invited)="outcomes.push($event); open.set(false)"
        (dismissed)="dismissals = dismissals + 1; open.set(false)"
      />
    }
  `,
})
class Host {
  readonly open = signal(true);
  readonly roles: readonly RoleOption[] = [
    { role: 'admin', label: 'admin' },
    { role: 'member', label: 'member' },
  ];
  readonly outcomes: InvitationOutcome[] = [];
  dismissals = 0;
}

describe('InviteMemberDialog', () => {
  let port: FakeUsersPort;
  let fixture: ComponentFixture<Host>;
  let root: HTMLElement;

  beforeEach(async () => {
    port = new FakeUsersPort();
    TestBed.configureTestingModule({
      providers: [provideTestI18n(), { provide: UsersPort, useValue: port }],
    });
    fixture = TestBed.createComponent(Host);
    root = fixture.nativeElement as HTMLElement;
    await fixture.whenStable();
  });

  function field(id: string): HTMLInputElement {
    return root.querySelector<HTMLInputElement>(`#${id}`)!;
  }

  function roleControl(): HTMLSelectElement {
    return root.querySelector<HTMLSelectElement>('#invite-role')!;
  }

  function submitButton(): HTMLButtonElement {
    return root.querySelector<HTMLButtonElement>('button[type="submit"]')!;
  }

  function text(selector: string): string {
    return root.querySelector(selector)?.textContent.replace(/\s+/g, ' ').trim() ?? '';
  }

  async function type(id: string, value: string): Promise<void> {
    field(id).value = value;
    field(id).dispatchEvent(new Event('input'));
    await fixture.whenStable();
  }

  async function fillIn(name = 'Laura Méndez', email = 'laura@example.com'): Promise<void> {
    await type('invite-full-name', name);
    await type('invite-email', email);
  }

  async function send(): Promise<void> {
    submitButton().click();
    fixture.detectChanges();
    await Promise.resolve();
  }

  async function settled(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve));
    await fixture.whenStable();
  }

  it('opens as a modal named by its title', () => {
    const dialog = root.querySelector('dialog')!;

    expect(dialog.open).toBeTrue();
    expect(dialog.getAttribute('aria-labelledby')).toBe('invite-member-title');
    expect(text('#invite-member-title')).toBe('Invitar miembro');
  });

  it('asks for the name, the email and the role, each with its label', () => {
    expect(text('label[for="invite-full-name"]')).toBe('Nombre');
    expect(text('label[for="invite-email"]')).toBe('Correo electrónico');
    expect(text('label[for="invite-role"]')).toBe('Rol');
  });

  it('proposes Member as the role', () => {
    expect(roleControl().value).toBe('member');
    expect(roleControl().selectedOptions[0]?.textContent.trim()).toBe('Miembro');
    expect(Array.from(roleControl().options).map((option) => option.textContent.trim())).toEqual([
      'Administrador',
      'Miembro',
    ]);
  });

  it('cannot be sent until both fields are valid, and shows no error before typing', async () => {
    expect(submitButton().disabled).toBeTrue();
    expect(text('#invite-full-name-problem')).toBe('');

    await type('invite-full-name', '   ');
    await type('invite-email', 'laura');

    expect(submitButton().disabled).toBeTrue();
    expect(text('#invite-full-name-problem')).toBe('Escribe el nombre de la persona.');
    expect(text('#invite-email-problem')).toBe(
      'Escribe un correo válido, como nombre@ejemplo.com.',
    );
    expect(field('invite-email').getAttribute('aria-invalid')).toBe('true');
    expect(field('invite-email').getAttribute('aria-describedby')).toBe('invite-email-problem');
  });

  it('sends the invitation as Member unless another role is chosen', async () => {
    await fillIn();

    await send();
    port.pending.next('invitation_sent');
    port.pending.complete();
    await settled();

    expect(port.invitations).toEqual([
      ['atlas', { fullName: 'Laura Méndez', email: 'laura@example.com', role: 'member' }],
    ]);
    expect(fixture.componentInstance.outcomes).toEqual(['invitation_sent']);
  });

  it('sends the role the admin chose', async () => {
    await fillIn();
    roleControl().value = 'admin';
    roleControl().dispatchEvent(new Event('change'));
    await fixture.whenStable();

    await send();

    expect(port.invitations[0]?.[1].role).toBe('admin');
  });

  it('cannot be sent twice while it is sending', async () => {
    await fillIn();

    await send();
    await fixture.whenStable();

    expect(submitButton().disabled).toBeTrue();
    expect(submitButton().textContent.trim()).toBe('Enviando…');
    submitButton().click();
    expect(port.invitations.length).toBe(1);
  });

  it('cannot be cancelled while it is sending, so the page always learns the outcome', async () => {
    await fillIn();

    await send();
    await fixture.whenStable();
    const cancel = Array.from(root.querySelectorAll('button')).find(
      (button) => button.textContent.trim() === 'Cancelar',
    )!;
    const escape = new Event('cancel', { cancelable: true });
    root.querySelector('dialog')!.dispatchEvent(escape);

    expect(cancel.disabled).toBeTrue();
    expect(escape.defaultPrevented).toBeTrue();
    port.pending.next('invitation_sent');
    port.pending.complete();
    await settled();
    expect(fixture.componentInstance.outcomes).toEqual(['invitation_sent']);
    expect(fixture.componentInstance.dismissals).toBe(0);
  });

  it('announces why the API refused the invitation and stays open', async () => {
    await fillIn();

    await send();
    port.pending.error(new MemberFailure('already_member'));
    await settled();

    expect(text('[role="alert"]')).toBe('Esta persona ya es integrante del equipo.');
    expect(root.querySelector('dialog')?.open).toBeTrue();
    expect(fixture.componentInstance.outcomes).toEqual([]);
    expect(submitButton().disabled).toBeFalse();
  });

  it('explains a disabled account and a mail server that does not answer', async () => {
    await fillIn();
    await send();
    port.pending.error(new MemberFailure('account_disabled'));
    await settled();
    expect(text('[role="alert"]')).toBe(
      'La cuenta de esta persona está desactivada, así que no se puede agregar al equipo.',
    );

    await send();
    port.pending.error(new Error('502'));
    await settled();
    expect(text('[role="alert"]')).toBe('No se pudo enviar la invitación. Inténtalo de nuevo.');
  });

  it('tells the page when it is cancelled', async () => {
    const cancel = Array.from(root.querySelectorAll('button')).find(
      (button) => button.textContent.trim() === 'Cancelar',
    )!;

    cancel.click();
    await fixture.whenStable();

    expect(fixture.componentInstance.dismissals).toBe(1);
    expect(root.querySelector('dialog')).toBeNull();
    expect(port.invitations).toEqual([]);
  });
});
