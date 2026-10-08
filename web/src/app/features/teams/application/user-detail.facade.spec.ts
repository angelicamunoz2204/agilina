import { TestBed } from '@angular/core/testing';
import { NEVER, type Observable, of, throwError } from 'rxjs';

import { UserDetailFacade } from './user-detail.facade';
import { UsersPort } from './users.port';
import { MemberFailure } from '../domain/member-failure';
import { type TeamMember } from '../domain/team-member';

const BRUNO: TeamMember = {
  userId: 'bruno',
  fullName: 'Bruno Díaz',
  email: 'bruno@example.com',
  role: 'member',
  label: 'member',
  joinedAt: new Date('2026-10-09T10:00:00Z'),
  roleChangeBlockedBy: null,
  removalBlockedBy: null,
};

class FakeUsersPort extends UsersPort {
  answer: TeamMember | MemberFailure | 'slow' = BRUNO;
  readonly asked: [string, string][] = [];

  list(): Observable<never> {
    return NEVER;
  }

  get(teamId: string, userId: string): Observable<TeamMember> {
    this.asked.push([teamId, userId]);
    const answer = this.answer;
    if (answer === 'slow') {
      return NEVER;
    }
    return answer instanceof MemberFailure ? throwError(() => answer) : of(answer);
  }

  me(): Observable<never> {
    return NEVER;
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

describe('UserDetailFacade', () => {
  let port: FakeUsersPort;

  beforeEach(() => {
    port = new FakeUsersPort();
    TestBed.configureTestingModule({
      providers: [UserDetailFacade, { provide: UsersPort, useValue: port }],
    });
  });

  function facade(): UserDetailFacade {
    return TestBed.inject(UserDetailFacade);
  }

  it('has nothing until it is told whom to read', () => {
    TestBed.tick();

    expect(facade().user()).toBeNull();
    expect(port.asked).toEqual([]);
  });

  it('asks the API for the user of the team and holds the answer', () => {
    facade().follow('atlas', 'bruno');
    TestBed.tick();

    expect(port.asked).toEqual([['atlas', 'bruno']]);
    expect(facade().user()).toEqual(BRUNO);
    expect(facade().problem()).toBeNull();
  });

  it('is loading while the API has not answered', () => {
    port.answer = 'slow';

    facade().follow('atlas', 'bruno');
    TestBed.tick();

    expect(facade().loading()).toBeTrue();
    expect(facade().user()).toBeNull();
  });

  it('says what went wrong when the user cannot be read', () => {
    port.answer = new MemberFailure('not_found');

    facade().follow('atlas', 'bruno');
    TestBed.tick();

    expect(facade().problem()).toBe('not_found');
    expect(facade().user()).toBeNull();
  });
});
