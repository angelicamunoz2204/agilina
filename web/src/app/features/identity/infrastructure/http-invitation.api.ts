import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, type Observable, throwError } from 'rxjs';

import { RUNTIME_CONFIG } from '@core/config/runtime-config';

import { type InvitationPort } from '../application/invitation.port';
import { type ActivatedAccount, type Invitation, type TeamRole } from '../domain/invitation';
import {
  InvitationFailure,
  type InvitationFailureKind,
  type PasswordRejection,
} from '../domain/invitation-failure';

/** Bodies of the API, exactly as it sends them. */
interface StatusResponse {
  email: string;
  full_name: string;
  role: string;
  status: string;
  expires_at: string;
}

interface ActivatedResponse {
  email: string;
  team_id: string;
  role: string;
}

/** Every error of the API has a stable `code`; a refused password also lists its `reasons`. */
interface ErrorResponse {
  code?: string;
  reasons?: string[];
}

const FAILURES: Readonly<Record<string, InvitationFailureKind>> = {
  invitation_not_found: 'not_found',
  invitation_used: 'used',
  invitation_expired: 'expired',
  invitation_revoked: 'revoked',
  account_already_exists: 'account_exists',
  password_policy: 'password_rejected',
  password_mismatch: 'password_mismatch',
  invitation_still_valid: 'still_valid',
  no_admins_to_notify: 'no_admins',
};

const REJECTIONS: readonly string[] = ['min_length', 'not_username', 'not_email'];

/**
 * HTTP adapter of the invitation port: the only exit of this feature towards the API. The
 * token goes in the body, never in the URL, so that it does not end up in any log.
 */
@Injectable()
export class HttpInvitationApi implements InvitationPort {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${inject(RUNTIME_CONFIG).apiUrl}/v1/invitations`;

  status(token: string): Observable<Invitation> {
    return this.http
      .post<StatusResponse>(`${this.baseUrl}/status`, { token })
      .pipe(map(toInvitation), catchError(failWithDomainError));
  }

  activate(token: string, password: string, confirmation: string): Observable<ActivatedAccount> {
    return this.http
      .post<ActivatedResponse>(`${this.baseUrl}/activate`, { token, password, confirmation })
      .pipe(map(toActivatedAccount), catchError(failWithDomainError));
  }

  requestNew(token: string): Observable<void> {
    return this.http.post(`${this.baseUrl}/request-new`, { token }).pipe(
      map(() => undefined),
      catchError(failWithDomainError),
    );
  }
}

function toInvitation(response: StatusResponse): Invitation {
  return {
    email: response.email,
    fullName: response.full_name,
    role: toRole(response.role),
    expiresAt: new Date(response.expires_at),
  };
}

function toActivatedAccount(response: ActivatedResponse): ActivatedAccount {
  return { email: response.email, teamId: response.team_id, role: toRole(response.role) };
}

function toRole(role: string): TeamRole {
  return role === 'admin' ? 'admin' : 'member';
}

/** The API contract stays in this file: the rest of the app only sees `InvitationFailure`. */
function failWithDomainError(error: unknown): Observable<never> {
  return throwError(() => toFailure(error));
}

function toFailure(error: unknown): InvitationFailure {
  if (!(error instanceof HttpErrorResponse)) {
    return new InvitationFailure('unavailable');
  }
  const body = asErrorResponse(error.error);
  const kind = (body.code !== undefined ? FAILURES[body.code] : undefined) ?? 'unavailable';
  return new InvitationFailure(kind, toRejections(body.reasons));
}

function asErrorResponse(body: unknown): ErrorResponse {
  return typeof body === 'object' && body !== null ? body : {};
}

/** A rule this screen does not know about still counts as a refusal: it shows as `other`. */
function toRejections(reasons: string[] | undefined): PasswordRejection[] {
  return (reasons ?? []).map((reason) =>
    REJECTIONS.includes(reason) ? (reason as PasswordRejection) : 'other',
  );
}
