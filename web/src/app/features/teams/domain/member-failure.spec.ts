import { MemberFailure, memberFailureKindOf } from './member-failure';

describe('memberFailureKindOf', () => {
  it('keeps the kind of a member failure', () => {
    expect(memberFailureKindOf(new MemberFailure('last_admin'))).toBe('last_admin');
    expect(memberFailureKindOf(new MemberFailure('forbidden'))).toBe('forbidden');
  });

  it('treats any other error as the service being unavailable', () => {
    expect(memberFailureKindOf(new Error('boom'))).toBe('unavailable');
    expect(memberFailureKindOf(undefined)).toBe('unavailable');
  });

  it('names the failure after its kind', () => {
    const failure = new MemberFailure('sprint_in_progress');

    expect(failure.name).toBe('MemberFailure');
    expect(failure.message).toBe('Member failure: sprint_in_progress');
  });
});
