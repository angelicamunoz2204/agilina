import { problemMessageKey } from './problem-message';

describe('problemMessageKey', () => {
  it('has no message when nothing went wrong', () => {
    expect(problemMessageKey(null)).toBeNull();
  });

  it('uses the generic failure text for an unexpected problem', () => {
    expect(problemMessageKey('unavailable')).toBe('failed');
  });

  it('uses a specific text for a known problem', () => {
    expect(problemMessageKey('not_authenticated')).toBe('problems.not_authenticated');
  });
});

describe('problemMessageKey for the members of a team', () => {
  it('uses a specific text for each known problem of a member', () => {
    expect(problemMessageKey('last_admin')).toBe('problems.last_admin');
    expect(problemMessageKey('already_member')).toBe('problems.already_member');
  });
});
