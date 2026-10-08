import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { provideTestRuntimeConfig, TEST_RUNTIME_CONFIG } from '@testing/runtime-config';

import { HttpUsersApi } from './http-users.api';
import { MemberFailure } from '../domain/member-failure';
import {
  type InvitationOutcome,
  type MyMembership,
  type TeamMember,
  type TeamMembers,
} from '../domain/team-member';

describe('HttpUsersApi', () => {
  const usersUrl = `${TEST_RUNTIME_CONFIG.apiUrl}/v1/users`;
  let api: HttpUsersApi;
  let backend: HttpTestingController;

  /** The request to `/v1/users{path}` that names this team in the query. */
  function expectUsers(path = '', team = 'atlas') {
    return backend.expectOne(
      (request) => request.url === `${usersUrl}${path}` && request.params.get('team_id') === team,
    );
  }

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        HttpUsersApi,
        provideHttpClient(),
        provideHttpClientTesting(),
        provideTestRuntimeConfig(),
      ],
    });
    api = TestBed.inject(HttpUsersApi);
    backend = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    backend.verify();
  });

  it('lists the members and the roles and maps them to the domain', () => {
    let received: TeamMembers | undefined;
    api.list('atlas').subscribe((members) => (received = members));

    const request = expectUsers();
    expect(request.request.method).toBe('GET');
    request.flush({
      roles: [
        { role: 'admin', label: 'admin' },
        { role: 'member', label: 'member' },
      ],
      users: [
        {
          user_id: 'ana',
          full_name: 'Ana Gil',
          email: 'ana@example.com',
          role: 'admin',
          label: 'admin',
          joined_at: '2026-10-08T15:04:05Z',
          role_change_blocked_by: 'sprint_in_progress',
          removal_blocked_by: 'last_admin',
        },
        {
          user_id: 'bruno',
          full_name: 'Bruno Díaz',
          email: 'bruno@example.com',
          role: 'member',
          label: 'member',
          joined_at: '2026-10-09T10:00:00Z',
          role_change_blocked_by: null,
          removal_blocked_by: null,
        },
      ],
    });

    expect(received).toEqual({
      roles: [
        { role: 'admin', label: 'admin' },
        { role: 'member', label: 'member' },
      ],
      members: [
        {
          userId: 'ana',
          fullName: 'Ana Gil',
          email: 'ana@example.com',
          role: 'admin',
          label: 'admin',
          joinedAt: new Date('2026-10-08T15:04:05Z'),
          roleChangeBlockedBy: 'sprint_in_progress',
          removalBlockedBy: 'last_admin',
        },
        {
          userId: 'bruno',
          fullName: 'Bruno Díaz',
          email: 'bruno@example.com',
          role: 'member',
          label: 'member',
          joinedAt: new Date('2026-10-09T10:00:00Z'),
          roleChangeBlockedBy: null,
          removalBlockedBy: null,
        },
      ],
    });
  });

  it('reads one user with the team in the query', () => {
    let received: TeamMember | undefined;
    api.get('atlas', 'bruno').subscribe((member) => (received = member));

    const request = expectUsers('/bruno');
    expect(request.request.method).toBe('GET');
    request.flush({
      user_id: 'bruno',
      full_name: 'Bruno Díaz',
      email: 'bruno@example.com',
      role: 'member',
      label: 'member',
      joined_at: '2026-10-09T10:00:00Z',
      role_change_blocked_by: 'sprint_in_progress',
      removal_blocked_by: null,
    });

    expect(received?.fullName).toBe('Bruno Díaz');
    expect(received?.joinedAt).toEqual(new Date('2026-10-09T10:00:00Z'));
    expect(received?.roleChangeBlockedBy).toBe('sprint_in_progress');
  });

  it('reads the caller as a member of the team for the header', () => {
    let received: MyMembership | undefined;
    api.me('atlas').subscribe((me) => (received = me));

    const request = expectUsers('/me');
    expect(request.request.method).toBe('GET');
    request.flush({
      user_id: 'ana',
      full_name: 'Ana Gil',
      email: 'ana@example.com',
      role: 'admin',
      label: 'scrum_master',
      joined_at: '2026-10-08T15:04:05Z',
    });

    expect(received).toEqual({
      userId: 'ana',
      fullName: 'Ana Gil',
      email: 'ana@example.com',
      role: 'admin',
      label: 'scrum_master',
      joinedAt: new Date('2026-10-08T15:04:05Z'),
    });
  });

  it('reads a role or a label it does not know as the one that offers the least', () => {
    let received: TeamMembers | undefined;
    api.list('atlas').subscribe((members) => (received = members));

    expectUsers().flush({
      roles: [{ role: 'owner', label: 'product_owner' }],
      users: [],
    });

    expect(received?.roles).toEqual([{ role: 'member', label: 'member' }]);
  });

  it('invites with the name, the email and the role, and emits what the API did', () => {
    let outcome: InvitationOutcome | undefined;
    api
      .invite('atlas', { fullName: 'Laura', email: 'laura@example.com', role: 'member' })
      .subscribe((received) => (outcome = received));

    const request = expectUsers('/invitations');
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({
      full_name: 'Laura',
      email: 'laura@example.com',
      role: 'member',
    });
    request.flush({ outcome: 'member_added' }, { status: 201, statusText: 'Created' });

    expect(outcome).toBe('member_added');
  });

  it('changes a role sending only the new role', () => {
    let done = false;
    api.changeRole('atlas', 'bruno', 'admin').subscribe(() => (done = true));

    const request = expectUsers('/bruno');
    expect(request.request.method).toBe('PATCH');
    expect(request.request.body).toEqual({ role: 'admin' });
    request.flush(null, { status: 204, statusText: 'No Content' });

    expect(done).toBeTrue();
  });

  it('removes a member', () => {
    let done = false;
    api.remove('atlas', 'bruno').subscribe(() => (done = true));

    const request = expectUsers('/bruno');
    expect(request.request.method).toBe('DELETE');
    request.flush(null, { status: 204, statusText: 'No Content' });

    expect(done).toBeTrue();
  });

  it('escapes the team and the member ids in the path', () => {
    api.remove('a/b', 'c?d').subscribe();

    const request = expectUsers('/c%3Fd', 'a/b');
    expect(request.request.method).toBe('DELETE');
    request.flush(null, { status: 204, statusText: 'No Content' });
  });

  const codes: [string, number, string][] = [
    ['not_authenticated', 401, 'not_authenticated'],
    ['not_a_team_member', 403, 'forbidden'],
    ['not_a_team_admin', 403, 'forbidden'],
    ['member_not_found', 404, 'not_found'],
    ['already_a_team_member', 409, 'already_member'],
    ['account_disabled', 409, 'account_disabled'],
    ['last_admin', 409, 'last_admin'],
    ['sprint_in_progress', 409, 'sprint_in_progress'],
    ['invalid_email', 422, 'invalid_email'],
    ['invalid_full_name', 422, 'invalid_name'],
    ['mail_unavailable', 502, 'mail_unavailable'],
    ['pending_invitation_exists', 409, 'unavailable'],
    ['something_new', 500, 'unavailable'],
  ];

  for (const [code, status, kind] of codes) {
    it(`turns the API code ${code} into the failure ${kind}`, () => {
      let failure: unknown;
      api.changeRole('atlas', 'bruno', 'member').subscribe({
        error: (error: unknown) => (failure = error),
      });

      expectUsers('/bruno').flush({ error: { code } }, { status, statusText: 'x' });

      expect(failure).toEqual(new MemberFailure(kind as MemberFailure['kind']));
    });
  }

  it('treats an answer without a code as the service being unavailable', () => {
    const failures: unknown[] = [];
    const keep = (error: unknown): void => {
      failures.push(error);
    };
    api.list('atlas').subscribe({ error: keep });
    expectUsers().flush('Bad gateway', {
      status: 502,
      statusText: 'Bad Gateway',
    });
    api.remove('atlas', 'bruno').subscribe({ error: keep });
    expectUsers('/bruno').error(new ProgressEvent('network'));
    api
      .invite('atlas', { fullName: 'Laura', email: 'laura@example.com', role: 'admin' })
      .subscribe({ error: keep });
    expectUsers('/invitations').flush(null, { status: 500, statusText: 'x' });

    expect(failures).toEqual([
      new MemberFailure('unavailable'),
      new MemberFailure('unavailable'),
      new MemberFailure('unavailable'),
    ]);
  });
});
