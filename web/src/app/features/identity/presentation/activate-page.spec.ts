import { TestBed, type ComponentFixture } from '@angular/core/testing';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject, type Observable } from 'rxjs';

import { provideFakeLogger } from '@testing/fake-logger';
import { provideTestI18n } from '@testing/i18n';

import { ActivatePage } from './activate-page';
import { InvitationPort } from '../application/invitation.port';
import { LoginRedirectPort } from '../application/login-redirect.port';
import { type ActivatedAccount, type Invitation } from '../domain/invitation';
import { InvitationFailure, type InvitationFailureKind } from '../domain/invitation-failure';

const INVITATION: Invitation = {
  email: 'julian@example.test',
  fullName: 'Julián Torres',
  role: 'admin',
  expiresAt: new Date('2026-10-11T12:00:00Z'),
};
const PASSWORD = 'a-long-password-1';

class FakeInvitationPort extends InvitationPort {
  tokens: string[] = [];
  activations: { token: string; password: string; confirmation: string }[] = [];
  requests: string[] = [];
  statusReply = new Subject<Invitation>();
  activateReply = new Subject<ActivatedAccount>();
  requestReply = new Subject<void>();

  status(token: string): Observable<Invitation> {
    this.tokens.push(token);
    return this.statusReply;
  }

  activate(token: string, password: string, confirmation: string): Observable<ActivatedAccount> {
    this.activations.push({ token, password, confirmation });
    return this.activateReply;
  }

  requestNew(token: string): Observable<void> {
    this.requests.push(token);
    return this.requestReply;
  }
}

class FakeLoginRedirect extends LoginRedirectPort {
  hints: (string | undefined)[] = [];

  redirect(loginHint?: string): Promise<void> {
    this.hints.push(loginHint);
    return Promise.resolve();
  }
}

describe('ActivatePage', () => {
  let fixture: ComponentFixture<ActivatePage>;
  let invitations: FakeInvitationPort;
  let login: FakeLoginRedirect;
  let navigate: jasmine.Spy;

  function open(fragment: string | null): void {
    invitations = new FakeInvitationPort();
    login = new FakeLoginRedirect();
    navigate = jasmine.createSpy('navigate').and.resolveTo(true);
    TestBed.configureTestingModule({
      imports: [ActivatePage],
      providers: [
        provideTestI18n(),
        provideFakeLogger(),
        { provide: InvitationPort, useValue: invitations },
        { provide: LoginRedirectPort, useValue: login },
        { provide: ActivatedRoute, useValue: { snapshot: { fragment } } },
        { provide: Router, useValue: { navigate } },
      ],
    });
    fixture = TestBed.createComponent(ActivatePage);
    fixture.detectChanges();
  }

  const root = (): HTMLElement => fixture.nativeElement as HTMLElement;
  const text = (): string => root().textContent;

  async function settle(): Promise<void> {
    await fixture.whenStable();
  }

  function field(id: string): HTMLInputElement {
    return root().querySelector<HTMLInputElement>(`#${id}`)!;
  }

  function type(id: string, value: string): void {
    const input = field(id);
    input.value = value;
    input.dispatchEvent(new Event('input'));
  }

  function button(label: string): HTMLButtonElement {
    return Array.from(root().querySelectorAll('button')).find((candidate) =>
      candidate.textContent.includes(label),
    )!;
  }

  async function fail(subject: { error(error: unknown): void }, kind: InvitationFailureKind) {
    subject.error(new InvitationFailure(kind));
    await settle();
  }

  describe('the token', () => {
    it('is read from the fragment of the link and checked against the API', () => {
      open('t=the-token');

      expect(invitations.tokens).toEqual(['the-token']);
    });

    it('is removed from the address bar once it has been read', () => {
      open('t=the-token');

      expect(navigate).toHaveBeenCalledOnceWith([], jasmine.objectContaining({ replaceUrl: true }));
    });
  });

  describe('a valid link', () => {
    beforeEach(async () => {
      open('t=the-token');
      expect(text()).toContain('Comprobando tu invitación');
      invitations.statusReply.next(INVITATION);
      await settle();
    });

    it('asks for the password with its confirmation and says who it is for', () => {
      expect(text()).toContain('Activar cuenta');
      expect(text()).toContain('Invitación para: julian@example.test');
      expect(text()).toContain('Mínimo 12 caracteres');
      expect(field('password').type).toBe('password');
      expect(field('confirmation').type).toBe('password');
      expect(root().querySelector('label[for="password"]')?.textContent).toContain('Contraseña');
      expect(root().querySelector('label[for="confirmation"]')?.textContent).toContain(
        'Confirmar contraseña',
      );
    });

    it('does not ask the API when the two passwords differ', async () => {
      type('password', PASSWORD);
      type('confirmation', 'another-password');
      button('Activar y entrar').click();
      await settle();

      expect(text()).toContain('Las contraseñas no coinciden.');
      expect(invitations.activations).toEqual([]);
    });

    it('activates and goes on to the sign-in with the email filled in', async () => {
      type('password', PASSWORD);
      type('confirmation', PASSWORD);
      button('Activar y entrar').click();
      invitations.activateReply.next({
        email: 'julian@example.test',
        teamId: 'team-1',
        role: 'admin',
      });
      await settle();

      expect(invitations.activations).toEqual([
        { token: 'the-token', password: PASSWORD, confirmation: PASSWORD },
      ]);
      expect(text()).toContain('Cuenta activada');
      expect(login.hints).toEqual(['julian@example.test']);
    });

    it('shows why the password was refused, one reason per rule', async () => {
      type('password', 'short');
      type('confirmation', 'short');
      button('Activar y entrar').click();
      invitations.activateReply.error(
        new InvitationFailure('password_rejected', ['min_length', 'not_email']),
      );
      await settle();

      expect(text()).toContain('Debe tener al menos 12 caracteres.');
      expect(text()).toContain('No puede ser igual a tu correo electrónico.');
      expect(root().querySelector('[role="alert"]')).not.toBeNull();
    });

    it('offers to sign in when the email already has an account', async () => {
      type('password', PASSWORD);
      type('confirmation', PASSWORD);
      button('Activar y entrar').click();
      await fail(invitations.activateReply, 'account_exists');

      expect(text()).toContain('Ya existe una cuenta con este correo');
      button('Iniciar sesión').click();
      expect(login.hints).toEqual(['julian@example.test']);
    });
  });

  describe('a link that cannot be used', () => {
    const cases: [InvitationFailureKind, string][] = [
      ['used', 'Este enlace ya se usó'],
      ['expired', 'Este enlace venció'],
      ['revoked', 'Esta invitación fue cancelada'],
    ];

    cases.forEach(([kind, title]) => {
      it(`says "${title}" and offers a new invitation`, async () => {
        open('t=the-token');
        await fail(invitations.statusReply, kind);

        expect(text()).toContain(title);
        expect(button('Solicitar una invitación nueva')).toBeDefined();
        expect(root().querySelector('form')).toBeNull();
      });
    });

    it('tells the admins when asked and confirms it', async () => {
      open('t=the-token');
      await fail(invitations.statusReply, 'expired');

      button('Solicitar una invitación nueva').click();
      invitations.requestReply.next();
      await settle();

      expect(invitations.requests).toEqual(['the-token']);
      expect(text()).toContain('avisamos a los administradores de tu equipo');
      expect(root().querySelector('[role="status"]')).not.toBeNull();
    });

    it('explains why the notice could not be sent', async () => {
      open('t=the-token');
      await fail(invitations.statusReply, 'expired');

      button('Solicitar una invitación nueva').click();
      await fail(invitations.requestReply, 'no_admins');

      expect(text()).toContain('no tiene administradores activos');
    });

    it('lets a person with a used link sign in', async () => {
      open('t=the-token');
      await fail(invitations.statusReply, 'used');

      button('Iniciar sesión').click();

      expect(login.hints).toEqual([undefined]);
    });

    it('names an altered link and sends the person back to the email, with nothing to request', async () => {
      open('t=altered');
      await fail(invitations.statusReply, 'not_found');

      expect(text()).toContain('Este enlace no es válido');
      expect(text()).toContain('pide una invitación nueva a tu administrador');
      expect(root().querySelector('button')).toBeNull();
    });

    it('says the same when the link has no token at all', async () => {
      open(null);
      await settle();

      expect(invitations.tokens).toEqual([]);
      expect(text()).toContain('Este enlace no es válido');
    });
  });

  describe('when the service does not answer', () => {
    it('says so and checks again on demand', async () => {
      open('t=the-token');
      await fail(invitations.statusReply, 'unavailable');

      expect(text()).toContain('No pudimos comprobar tu invitación');
      button('Reintentar').click();
      await settle();

      expect(invitations.tokens).toEqual(['the-token', 'the-token']);
    });
  });
});
