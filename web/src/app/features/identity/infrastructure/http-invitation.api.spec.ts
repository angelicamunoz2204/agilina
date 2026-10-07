import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { provideTestRuntimeConfig, TEST_RUNTIME_CONFIG } from '@testing/runtime-config';

import { HttpInvitationApi } from './http-invitation.api';
import { InvitationFailure, type InvitationFailureKind } from '../domain/invitation-failure';

const BASE = `${TEST_RUNTIME_CONFIG.apiUrl}/v1/invitations`;

describe('HttpInvitationApi', () => {
  let api: HttpInvitationApi;
  let backend: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        HttpInvitationApi,
        provideHttpClient(),
        provideHttpClientTesting(),
        provideTestRuntimeConfig(),
      ],
    });
    api = TestBed.inject(HttpInvitationApi);
    backend = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    backend.verify();
  });

  /** The failure the adapter turns an error answer into, or the value it did not throw. */
  function failureOf(call: ReturnType<HttpInvitationApi['status']>, answer: () => void): unknown {
    let received: unknown;
    call.subscribe({
      next: () => {
        received = 'no error';
      },
      error: (error: unknown) => (received = error),
    });
    answer();
    return received;
  }

  it('asks for the status with the token in the body, never in the URL', () => {
    let received: unknown;
    api.status('the-token').subscribe((invitation) => (received = invitation));

    const request = backend.expectOne(`${BASE}/status`);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ token: 'the-token' });
    expect(request.request.urlWithParams).not.toContain('the-token');
    request.flush({
      email: 'julian@example.test',
      full_name: 'Julián Torres',
      role: 'admin',
      status: 'pending',
      expires_at: '2026-10-11T12:00:00Z',
    });

    expect(received).toEqual({
      email: 'julian@example.test',
      fullName: 'Julián Torres',
      role: 'admin',
      expiresAt: new Date('2026-10-11T12:00:00Z'),
    });
  });

  it('activates with the password and its confirmation and maps the account', () => {
    let received: unknown;
    api.activate('the-token', 'a-long-password-1', 'a-long-password-1').subscribe((account) => {
      received = account;
    });

    const request = backend.expectOne(`${BASE}/activate`);
    expect(request.request.body).toEqual({
      token: 'the-token',
      password: 'a-long-password-1',
      confirmation: 'a-long-password-1',
    });
    request.flush(
      { email: 'julian@example.test', team_id: 'team-1', role: 'member' },
      { status: 201, statusText: 'Created' },
    );

    expect(received).toEqual({ email: 'julian@example.test', teamId: 'team-1', role: 'member' });
  });

  it('asks the admins for a new invitation', () => {
    let done = false;
    api.requestNew('the-token').subscribe(() => (done = true));

    const request = backend.expectOne(`${BASE}/request-new`);
    expect(request.request.body).toEqual({ token: 'the-token' });
    request.flush({ status: 'requested' }, { status: 202, statusText: 'Accepted' });

    expect(done).toBeTrue();
  });

  const answers: [number, string, InvitationFailureKind][] = [
    [404, 'invitation_not_found', 'not_found'],
    [410, 'invitation_used', 'used'],
    [410, 'invitation_expired', 'expired'],
    [410, 'invitation_revoked', 'revoked'],
    [409, 'account_already_exists', 'account_exists'],
    [422, 'password_mismatch', 'password_mismatch'],
    [409, 'invitation_still_valid', 'still_valid'],
    [409, 'no_admins_to_notify', 'no_admins'],
    [503, 'identity_provider_unavailable', 'unavailable'],
    [502, 'mail_unavailable', 'unavailable'],
    [500, 'something_new', 'unavailable'],
  ];

  answers.forEach(([status, code, kind]) => {
    it(`turns the code ${code} (${String(status)}) into the failure ${kind}`, () => {
      const failure = failureOf(api.status('t'), () => {
        backend
          .expectOne(`${BASE}/status`)
          .flush({ error: { code } }, { status, statusText: 'Error' });
      });

      expect(failure).toBeInstanceOf(InvitationFailure);
      expect((failure as InvitationFailure).kind).toBe(kind);
    });
  });

  it('keeps the rules of the password policy that were broken', () => {
    let received: unknown;
    api
      .activate('t', 'short', 'short')
      .subscribe({ error: (error: unknown) => (received = error) });

    backend.expectOne(`${BASE}/activate`).flush(
      {
        error: {
          code: 'password_policy',
          details: { reasons: ['min_length', 'not_email', 'a_rule_from_the_future'] },
        },
      },
      { status: 422, statusText: 'Unprocessable Entity' },
    );

    expect(received).toBeInstanceOf(InvitationFailure);
    expect((received as InvitationFailure).kind).toBe('password_rejected');
    expect((received as InvitationFailure).reasons).toEqual(['min_length', 'not_email', 'other']);
  });

  it('says the service is unavailable when it cannot be reached or answers with no body', () => {
    const unreachable = failureOf(api.status('t'), () => {
      backend.expectOne(`${BASE}/status`).error(new ProgressEvent('error'));
    });
    expect((unreachable as InvitationFailure).kind).toBe('unavailable');

    const empty = failureOf(api.status('t'), () => {
      backend.expectOne(`${BASE}/status`).flush('', { status: 502, statusText: 'Bad Gateway' });
    });
    expect((empty as InvitationFailure).kind).toBe('unavailable');
  });
});
