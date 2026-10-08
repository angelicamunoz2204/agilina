import { TestBed } from '@angular/core/testing';
import { NEVER, Subject, type Observable } from 'rxjs';

import { InviteMemberFacade } from './invite-member.facade';
import { UsersPort } from './users.port';
import { MemberFailure } from '../domain/member-failure';
import { type InvitationOutcome, type MemberInvitation } from '../domain/team-member';

const LAURA: MemberInvitation = { fullName: 'Laura', email: 'laura@example.com', role: 'member' };

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

  answer(outcome: InvitationOutcome): void {
    this.pending.next(outcome);
    this.pending.complete();
  }
}

describe('InviteMemberFacade', () => {
  let port: FakeUsersPort;
  let facade: InviteMemberFacade;

  beforeEach(() => {
    port = new FakeUsersPort();
    TestBed.configureTestingModule({
      providers: [InviteMemberFacade, { provide: UsersPort, useValue: port }],
    });
    facade = TestBed.inject(InviteMemberFacade);
  });

  it('sends the invitation to the team and resolves to what it did', async () => {
    const invited = facade.invite('atlas', LAURA);
    port.answer('invitation_sent');

    expect(await invited).toBe('invitation_sent');
    expect(port.invitations).toEqual([['atlas', LAURA]]);
    expect(facade.outcome()).toBe('invitation_sent');
    expect(facade.failed()).toBeFalse();
  });

  it('is saving until the API answers', async () => {
    const invited = facade.invite('atlas', LAURA);
    expect(facade.saving()).toBeTrue();

    port.answer('member_added');
    await invited;

    expect(facade.saving()).toBeFalse();
    expect(facade.outcome()).toBe('member_added');
  });

  it('resolves to null and keeps the problem when the API refuses it', async () => {
    const invited = facade.invite('atlas', LAURA);
    port.pending.error(new MemberFailure('already_member'));

    expect(await invited).toBeNull();
    expect(facade.failed()).toBeTrue();
    expect(facade.problem()).toBe('already_member');
    expect(facade.saving()).toBeFalse();
  });

  it('forgets the last problem when trying again', async () => {
    const refused = facade.invite('atlas', LAURA);
    port.pending.error(new Error('502'));
    await refused;
    expect(facade.problem()).toBe('unavailable');

    const retried = facade.invite('atlas', LAURA);
    expect(facade.problem()).toBeNull();
    port.answer('invitation_sent');

    expect(await retried).toBe('invitation_sent');
  });
});
