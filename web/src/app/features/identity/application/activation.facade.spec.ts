import { TestBed } from '@angular/core/testing';
import { Subject, type Observable } from 'rxjs';

import { Logger } from '@core/logging/logger';
import { provideFakeLogger, type FakeLogger } from '@testing/fake-logger';

import { ActivationFacade } from './activation.facade';
import { InvitationPort } from './invitation.port';
import { LoginRedirectPort } from './login-redirect.port';
import { type ActivatedAccount, type Invitation } from '../domain/invitation';
import { InvitationFailure, type InvitationFailureKind } from '../domain/invitation-failure';

const INVITATION: Invitation = {
  email: 'julian@example.test',
  fullName: 'Julián Torres',
  role: 'admin',
  expiresAt: new Date('2026-10-11T12:00:00Z'),
};
const ACCOUNT: ActivatedAccount = { email: 'julian@example.test', teamId: 'team-1', role: 'admin' };
const PASSWORD = 'a-long-password-1';

/** Port double: each call waits until the test answers it. */
class FakeInvitationPort extends InvitationPort {
  statusCalls: string[] = [];
  activations: { token: string; password: string; confirmation: string }[] = [];
  requests: string[] = [];
  statusReply = new Subject<Invitation>();
  activateReply = new Subject<ActivatedAccount>();
  requestReply = new Subject<void>();

  status(token: string): Observable<Invitation> {
    this.statusCalls.push(token);
    this.statusReply = new Subject<Invitation>();
    return this.statusReply;
  }

  activate(token: string, password: string, confirmation: string): Observable<ActivatedAccount> {
    this.activations.push({ token, password, confirmation });
    this.activateReply = new Subject<ActivatedAccount>();
    return this.activateReply;
  }

  requestNew(token: string): Observable<void> {
    this.requests.push(token);
    this.requestReply = new Subject<void>();
    return this.requestReply;
  }
}

class FakeLoginRedirect extends LoginRedirectPort {
  hints: (string | undefined)[] = [];
  fails = false;

  redirect(loginHint?: string): Promise<void> {
    this.hints.push(loginHint);
    return this.fails ? Promise.reject(new Error('blocked')) : Promise.resolve();
  }
}

describe('ActivationFacade', () => {
  let facade: ActivationFacade;
  let invitations: FakeInvitationPort;
  let login: FakeLoginRedirect;

  beforeEach(() => {
    invitations = new FakeInvitationPort();
    login = new FakeLoginRedirect();
    TestBed.configureTestingModule({
      providers: [
        ActivationFacade,
        provideFakeLogger(),
        { provide: InvitationPort, useValue: invitations },
        { provide: LoginRedirectPort, useValue: login },
      ],
    });
    facade = TestBed.inject(ActivationFacade);
  });

  function openValidLink(): void {
    facade.open('the-token');
    invitations.statusReply.next(INVITATION);
  }

  function failWith(subject: { error(error: unknown): void }, kind: InvitationFailureKind): void {
    subject.error(new InvitationFailure(kind));
  }

  describe('opening the link', () => {
    it('checks the token and shows the form for a valid link', () => {
      facade.open('the-token');
      expect(facade.phase()).toBe('checking');

      invitations.statusReply.next(INVITATION);

      expect(invitations.statusCalls).toEqual(['the-token']);
      expect(facade.phase()).toBe('form');
      expect(facade.invitation()).toEqual(INVITATION);
    });

    it('does not even ask the API when the link has no token', () => {
      facade.open(null);

      expect(invitations.statusCalls).toEqual([]);
      expect(facade.phase()).toBe('link_problem');
      expect(facade.linkProblem()).toBe('not_found');
      expect(facade.canRequestNew()).toBeFalse();
    });

    (['used', 'expired', 'revoked'] as const).forEach((kind) => {
      it(`explains a ${kind} link and offers a new invitation`, () => {
        facade.open('the-token');

        failWith(invitations.statusReply, kind);

        expect(facade.phase()).toBe('link_problem');
        expect(facade.linkProblem()).toBe(kind);
        expect(facade.canRequestNew()).toBeTrue();
      });
    });

    it('explains an altered link but cannot ask anyone for a new one', () => {
      facade.open('altered');

      failWith(invitations.statusReply, 'not_found');

      expect(facade.linkProblem()).toBe('not_found');
      expect(facade.canRequestNew()).toBeFalse();
    });

    it('says the service is unavailable and tries the same link again on demand', () => {
      facade.open('the-token');
      failWith(invitations.statusReply, 'unavailable');
      expect(facade.phase()).toBe('unavailable');

      facade.retry();
      expect(facade.phase()).toBe('checking');
      invitations.statusReply.next(INVITATION);

      expect(invitations.statusCalls).toEqual(['the-token', 'the-token']);
      expect(facade.phase()).toBe('form');
    });

    it('treats an unexpected error as an unavailable service', () => {
      facade.open('the-token');

      invitations.statusReply.error(new Error('boom'));

      expect(facade.phase()).toBe('unavailable');
    });
  });

  describe('activating', () => {
    beforeEach(openValidLink);

    it('does not ask the API for an empty password or one that was not repeated', () => {
      facade.activate('', '');
      expect(facade.formProblem()).toBe('empty');

      facade.activate(PASSWORD, 'something else');
      expect(facade.formProblem()).toBe('mismatch');

      expect(invitations.activations).toEqual([]);
      expect(facade.phase()).toBe('form');
    });

    it('sends the token with the password and goes to the sign-in with the email', () => {
      facade.activate(PASSWORD, PASSWORD);
      expect(facade.phase()).toBe('submitting');

      invitations.activateReply.next(ACCOUNT);

      expect(invitations.activations).toEqual([
        { token: 'the-token', password: PASSWORD, confirmation: PASSWORD },
      ]);
      expect(facade.phase()).toBe('activated');
      expect(login.hints).toEqual(['julian@example.test']);
    });

    it('ignores a second submit while the first one is in flight', () => {
      facade.activate(PASSWORD, PASSWORD);
      facade.activate(PASSWORD, PASSWORD);

      expect(invitations.activations).toHaveSize(1);
    });

    it('shows the rules of the policy that the password broke and lets the person try again', () => {
      facade.activate('short', 'short');
      invitations.activateReply.error(
        new InvitationFailure('password_rejected', ['min_length', 'not_email']),
      );

      expect(facade.phase()).toBe('form');
      expect(facade.rejections()).toEqual(['min_length', 'not_email']);
      expect(login.hints).toEqual([]);

      facade.activate(PASSWORD, PASSWORD);
      expect(facade.rejections()).toEqual([]);
      expect(invitations.activations).toHaveSize(2);
    });

    it('says when the email already has an account', () => {
      facade.activate(PASSWORD, PASSWORD);

      failWith(invitations.activateReply, 'account_exists');

      expect(facade.phase()).toBe('form');
      expect(facade.formProblem()).toBe('account_exists');
    });

    it('moves to the link problem when the link was used in the meantime', () => {
      facade.activate(PASSWORD, PASSWORD);

      failWith(invitations.activateReply, 'used');

      expect(facade.phase()).toBe('link_problem');
      expect(facade.linkProblem()).toBe('used');
    });

    it('keeps the form and says it could not activate when the service fails', () => {
      facade.activate(PASSWORD, PASSWORD);

      failWith(invitations.activateReply, 'unavailable');

      expect(facade.phase()).toBe('form');
      expect(facade.formProblem()).toBe('unavailable');
    });

    it('shows a mismatch the server found as the same problem', () => {
      facade.activate(PASSWORD, PASSWORD);

      failWith(invitations.activateReply, 'password_mismatch');

      expect(facade.formProblem()).toBe('mismatch');
    });

    it('can go to the sign-in again, and reports it when it cannot', async () => {
      facade.activate(PASSWORD, PASSWORD);
      invitations.activateReply.next(ACCOUNT);
      login.fails = true;

      facade.goToLogin();
      await new Promise((resolve) => setTimeout(resolve));

      expect(facade.loginFailed()).toBeTrue();
      const logger = TestBed.inject(Logger) as FakeLogger;
      expect(logger.entries.map((entry) => entry.message)).toEqual([
        'Redirect to the sign-in failed',
      ]);
    });
  });

  describe('asking for a new invitation', () => {
    function openWithProblem(kind: InvitationFailureKind): void {
      facade.open('the-token');
      failWith(invitations.statusReply, kind);
    }

    it('tells the admins and says so', () => {
      openWithProblem('expired');

      facade.requestNew();
      expect(facade.request()).toBe('sending');
      invitations.requestReply.next();

      expect(invitations.requests).toEqual(['the-token']);
      expect(facade.request()).toBe('sent');
    });

    it('does not send twice', () => {
      openWithProblem('expired');

      facade.requestNew();
      facade.requestNew();

      expect(invitations.requests).toHaveSize(1);
    });

    (
      [
        ['no_admins', 'no_admins'],
        ['still_valid', 'still_valid'],
        ['unavailable', 'unavailable'],
        ['not_found', 'unavailable'],
      ] as const
    ).forEach(([kind, expected]) => {
      it(`reports ${kind} as ${expected}`, () => {
        openWithProblem('used');

        facade.requestNew();
        failWith(invitations.requestReply, kind);

        expect(facade.request()).toBe(expected);
      });
    });

    it('does nothing for an altered link: there is nobody to tell', () => {
      openWithProblem('not_found');

      facade.requestNew();

      expect(invitations.requests).toEqual([]);
      expect(facade.request()).toBe('idle');
    });

    it('goes to the sign-in without an email when it was never shown', () => {
      openWithProblem('used');

      facade.goToLogin();

      expect(login.hints).toEqual([undefined]);
    });
  });
});
