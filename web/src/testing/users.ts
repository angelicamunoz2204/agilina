import { type Provider } from '@angular/core';
import { NEVER, type Observable, of } from 'rxjs';

import { UsersPort } from '@features/teams/application/users.port';
import { type MyMembership } from '@features/teams/domain/team-member';

/**
 * A users port for the specs of screens that only need the caller as a member (the app
 * header): `me` answers an admin of a team in support mode and everything else never answers.
 */
export class StubUsersPort extends UsersPort {
  list(): Observable<never> {
    return NEVER;
  }

  get(): Observable<never> {
    return NEVER;
  }

  me(): Observable<MyMembership> {
    return of({
      userId: 'ana',
      fullName: 'Ana Gil',
      email: 'ana@example.com',
      role: 'admin',
      label: 'scrum_master',
      joinedAt: new Date('2026-10-08T15:04:05Z'),
    });
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

export function provideStubUsersPort(): Provider {
  return { provide: UsersPort, useClass: StubUsersPort };
}
