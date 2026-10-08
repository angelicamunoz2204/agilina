import { ApplicationRef, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { NEVER, of, Subject, throwError, type Observable } from 'rxjs';

import { TeamMembersFacade } from './team-members.facade';
import { UsersPort } from './users.port';
import { MemberFailure } from '../domain/member-failure';
import { type TeamMember, type TeamMembers, type TeamRole } from '../domain/team-member';

const ANA: TeamMember = {
  userId: 'ana',
  fullName: 'Ana Gil',
  email: 'ana@example.com',
  role: 'admin',
  label: 'admin',
  joinedAt: new Date('2026-10-08T15:04:05Z'),
  roleChangeBlockedBy: 'last_admin',
  removalBlockedBy: 'last_admin',
};
const BRUNO: TeamMember = {
  userId: 'bruno',
  fullName: 'Bruno Díaz',
  email: 'bruno@example.com',
  role: 'member',
  label: 'member',
  joinedAt: new Date('2026-10-08T15:04:05Z'),
  roleChangeBlockedBy: null,
  removalBlockedBy: null,
};
const ROLES = [
  { role: 'admin', label: 'admin' },
  { role: 'member', label: 'member' },
] as const;

/**
 * Port double: list() answers the members of each known team (and fails for any other);
 * changeRole() and remove() wait until the test answers them.
 */
class FakeUsersPort extends UsersPort {
  readonly listed: string[] = [];
  readonly changes: [string, string, TeamRole][] = [];
  readonly removals: [string, string][] = [];
  readonly teams: Record<string, TeamMembers> = {
    atlas: { roles: ROLES, members: [ANA, BRUNO] },
    boreal: { roles: ROLES, members: [ANA] },
  };
  pending = new Subject<void>();

  list(teamId: string): Observable<TeamMembers> {
    this.listed.push(teamId);
    const members = this.teams[teamId];
    return members === undefined ? throwError(() => new MemberFailure('forbidden')) : of(members);
  }

  get(): Observable<never> {
    return NEVER;
  }

  me(): Observable<never> {
    return NEVER;
  }

  invite(): Observable<never> {
    return NEVER;
  }

  changeRole(teamId: string, userId: string, role: TeamRole): Observable<void> {
    this.changes.push([teamId, userId, role]);
    this.pending = new Subject<void>();
    return this.pending;
  }

  remove(teamId: string, userId: string): Observable<void> {
    this.removals.push([teamId, userId]);
    this.pending = new Subject<void>();
    return this.pending;
  }

  accept(): void {
    this.pending.next();
    this.pending.complete();
  }

  refuse(failure: Error): void {
    this.pending.error(failure);
  }
}

describe('TeamMembersFacade', () => {
  let port: FakeUsersPort;
  let facade: TeamMembersFacade;

  beforeEach(() => {
    port = new FakeUsersPort();
    TestBed.configureTestingModule({
      providers: [TeamMembersFacade, { provide: UsersPort, useValue: port }],
    });
    facade = TestBed.inject(TeamMembersFacade);
  });

  async function stable(): Promise<void> {
    await TestBed.inject(ApplicationRef).whenStable();
  }

  async function following(teamId = 'atlas'): Promise<void> {
    facade.follow(signal(teamId));
    await stable();
  }

  it('asks for nothing until it knows which team to follow', async () => {
    await stable();

    expect(port.listed).toEqual([]);
    expect(facade.members()).toBeNull();
    expect(facade.roles()).toEqual([]);
  });

  it('loads the members and the roles of the team it follows', async () => {
    await following();

    expect(port.listed).toEqual(['atlas']);
    expect(facade.members()).toEqual([ANA, BRUNO]);
    expect(facade.roles()).toEqual(ROLES);
    expect(facade.loading()).toBeFalse();
    expect(facade.problem()).toBeNull();
  });

  it('loads them again when the team id changes', async () => {
    const teamId = signal('atlas');
    facade.follow(teamId);
    await stable();

    teamId.set('boreal');
    await stable();

    expect(port.listed).toEqual(['atlas', 'boreal']);
    expect(facade.members()).toEqual([ANA]);
  });

  it('turns a refused team into a problem the screen translates', async () => {
    await following('someone-elses');

    expect(facade.failed()).toBeTrue();
    expect(facade.problem()).toBe('forbidden');
    expect(facade.members()).toBeNull();
  });

  it('changes a role, is saving meanwhile and loads the list again', async () => {
    await following();

    const changed = facade.changeRole('bruno', 'admin');
    expect(facade.saving()).toBeTrue();
    expect(facade.savingMember()).toBe('bruno');
    port.accept();

    expect(await changed).toBeTrue();
    await stable();
    expect(port.changes).toEqual([['atlas', 'bruno', 'admin']]);
    expect(port.listed).toEqual(['atlas', 'atlas']);
    expect(facade.saving()).toBeFalse();
    expect(facade.roleChangeProblem()).toBeNull();
  });

  it('keeps the list and the reason when the API refuses a role change', async () => {
    await following();

    const changed = facade.changeRole('ana', 'member');
    port.refuse(new MemberFailure('last_admin'));

    expect(await changed).toBeFalse();
    await stable();
    expect(facade.roleChangeProblem()).toBe('last_admin');
    expect(facade.members()).toEqual([ANA, BRUNO]);
    expect(port.listed).toEqual(['atlas', 'atlas']);
  });

  it('removes a member and loads the list again', async () => {
    await following();

    const removed = facade.remove('bruno');
    port.accept();

    expect(await removed).toBeTrue();
    await stable();
    expect(port.removals).toEqual([['atlas', 'bruno']]);
    expect(port.listed).toEqual(['atlas', 'atlas']);
    expect(facade.removalProblem()).toBeNull();
  });

  it('keeps the reason when the API refuses a removal, until it is cleared', async () => {
    await following();

    const removed = facade.remove('ana');
    port.refuse(new Error('503'));

    expect(await removed).toBeFalse();
    expect(facade.removalProblem()).toBe('unavailable');
    facade.clearRemovalProblem();
    expect(facade.removalProblem()).toBeNull();
  });

  it('forgets the last problem when another change starts', async () => {
    await following();
    const refused = facade.changeRole('ana', 'member');
    port.refuse(new MemberFailure('last_admin'));
    await refused;

    const removed = facade.remove('bruno');

    expect(facade.roleChangeProblem()).toBeNull();
    port.accept();
    expect(await removed).toBeTrue();
  });

  it('does one change at a time', async () => {
    await following();

    const first = facade.changeRole('bruno', 'admin');
    const second = await facade.remove('bruno');

    expect(second).toBeFalse();
    expect(port.removals).toEqual([]);
    port.accept();
    expect(await first).toBeTrue();
  });

  it('changes nothing before it knows the team', async () => {
    expect(await facade.changeRole('bruno', 'admin')).toBeFalse();
    expect(await facade.remove('bruno')).toBeFalse();

    expect(port.changes).toEqual([]);
    expect(port.removals).toEqual([]);
  });

  it('loads the list again on demand', async () => {
    await following();

    facade.reload();
    await stable();

    expect(port.listed).toEqual(['atlas', 'atlas']);
  });
});
