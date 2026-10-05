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
