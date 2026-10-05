import { DestroyRef, computed, inject, Injectable, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

import { Logger } from '@core/logging/logger';

import { InvitationPort } from './invitation.port';
import { LoginRedirectPort } from './login-redirect.port';
import { type Invitation } from '../domain/invitation';
import { InvitationFailure, type PasswordRejection } from '../domain/invitation-failure';
import { checkPasswordInput, type PasswordInputProblem } from '../domain/password-input';

export type ActivationPhase =
  'checking' | 'form' | 'submitting' | 'link_problem' | 'unavailable' | 'activated';

/** Why a link cannot be used. Only the first three can ask for a new invitation. */
export type LinkProblem = 'not_found' | 'used' | 'expired' | 'revoked';

export type FormProblem = PasswordInputProblem | 'account_exists' | 'unavailable';

export type RequestState =
  'idle' | 'sending' | 'sent' | 'no_admins' | 'still_valid' | 'unavailable';

const LINK_PROBLEMS: readonly string[] = ['not_found', 'used', 'expired', 'revoked'];
const CAN_REQUEST_NEW: readonly LinkProblem[] = ['used', 'expired', 'revoked'];

/**
 * State of the activation screen: what the presentation reads and triggers. Provided by
 * the page, so it lives and dies with it.
 *
 * The token and the password stay in memory only for as long as the screen needs them.
 * The HTTP interceptor already logs failed requests, so they are not logged again here.
 */
@Injectable()
export class ActivationFacade {
  private readonly invitations = inject(InvitationPort);
  private readonly loginRedirect = inject(LoginRedirectPort);
  private readonly logger = inject(Logger);
  private readonly destroyRef = inject(DestroyRef);

  private token: string | null = null;
  private activatedEmail: string | null = null;

  private readonly phaseState = signal<ActivationPhase>('checking');
  private readonly invitationState = signal<Invitation | null>(null);
  private readonly linkProblemState = signal<LinkProblem | null>(null);
  private readonly formProblemState = signal<FormProblem | null>(null);
  private readonly rejectionsState = signal<readonly PasswordRejection[]>([]);
  private readonly requestState = signal<RequestState>('idle');
  private readonly loginFailedState = signal(false);

  readonly phase = this.phaseState.asReadonly();
  readonly invitation = this.invitationState.asReadonly();
  readonly linkProblem = this.linkProblemState.asReadonly();
  readonly formProblem = this.formProblemState.asReadonly();
  /** The rules of the password policy that the last attempt broke. */
  readonly rejections = this.rejectionsState.asReadonly();
  readonly request = this.requestState.asReadonly();
  readonly loginFailed = this.loginFailedState.asReadonly();

  /** A used or expired link can ask for another one; an altered link names nobody to tell. */
  readonly canRequestNew = computed(() => {
    const problem = this.linkProblemState();
    return this.token !== null && problem !== null && CAN_REQUEST_NEW.includes(problem);
  });

  /** Checks the link the person opened. `null` means there was no token in the URL. */
  open(token: string | null): void {
    this.token = token;
    if (token === null) {
      this.showLinkProblem('not_found');
      return;
    }
    this.phaseState.set('checking');
    this.invitations
      .status(token)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (invitation) => {
          this.invitationState.set(invitation);
          this.phaseState.set('form');
        },
        error: (error: unknown) => {
          const failure = asFailure(error);
          if (isLinkProblem(failure.kind)) {
            this.showLinkProblem(failure.kind);
          } else {
            this.phaseState.set('unavailable');
          }
        },
      });
  }

  /** Tries the same link again after the API could not be reached. */
  retry(): void {
    this.open(this.token);
  }

  activate(password: string, confirmation: string): void {
    const problem = checkPasswordInput(password, confirmation);
    if (problem !== null) {
      this.formProblemState.set(problem);
      this.rejectionsState.set([]);
      return;
    }
    if (this.token === null || this.phaseState() !== 'form') {
      return;
    }
    this.formProblemState.set(null);
    this.rejectionsState.set([]);
    this.phaseState.set('submitting');
    this.invitations
      .activate(this.token, password, confirmation)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (account) => {
          this.activatedEmail = account.email;
          this.phaseState.set('activated');
          this.goToLogin();
        },
        error: (error: unknown) => {
          this.showActivationFailure(asFailure(error));
        },
      });
  }

  /** Asks the team's admins for a new invitation. */
  requestNew(): void {
    if (this.token === null || !this.canRequestNew() || this.requestState() === 'sending') {
      return;
    }
    this.requestState.set('sending');
    this.invitations
      .requestNew(this.token)
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => {
          this.requestState.set('sent');
        },
        error: (error: unknown) => {
          this.requestState.set(requestFailure(asFailure(error)));
        },
      });
  }

  /** Sends the person to Keycloak's sign-in, with their email typed when it is known. */
  goToLogin(): void {
    const email = this.activatedEmail ?? this.invitationState()?.email;
    this.loginFailedState.set(false);
    this.loginRedirect.redirect(email).catch((error: unknown) => {
      this.logger.error('Redirect to the sign-in failed', error);
      this.loginFailedState.set(true);
    });
  }

  private showLinkProblem(problem: LinkProblem): void {
    this.linkProblemState.set(problem);
    this.phaseState.set('link_problem');
  }

  private showActivationFailure(failure: InvitationFailure): void {
    if (isLinkProblem(failure.kind)) {
      this.showLinkProblem(failure.kind);
      return;
    }
    this.phaseState.set('form');
    switch (failure.kind) {
      case 'password_rejected':
        this.rejectionsState.set(failure.reasons);
        break;
      case 'account_exists':
        this.formProblemState.set('account_exists');
        break;
      case 'password_mismatch':
        this.formProblemState.set('mismatch');
        break;
      default:
        this.formProblemState.set('unavailable');
    }
  }
}

function asFailure(error: unknown): InvitationFailure {
  return error instanceof InvitationFailure ? error : new InvitationFailure('unavailable');
}

function isLinkProblem(kind: string): kind is LinkProblem {
  return LINK_PROBLEMS.includes(kind);
}

function requestFailure(failure: InvitationFailure): RequestState {
  switch (failure.kind) {
    case 'no_admins':
      return 'no_admins';
    case 'still_valid':
      return 'still_valid';
    default:
      return 'unavailable';
  }
}
