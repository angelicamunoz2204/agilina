import { failureKindOf, TeamFailure } from './team-failure';

describe('failureKindOf', () => {
  it('keeps the kind of a team failure', () => {
    expect(failureKindOf(new TeamFailure('not_authenticated'))).toBe('not_authenticated');
  });

  it('treats any other error as the service being unavailable', () => {
    expect(failureKindOf(new Error('boom'))).toBe('unavailable');
    expect(failureKindOf(undefined)).toBe('unavailable');
  });
});
