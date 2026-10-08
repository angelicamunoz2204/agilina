import { SprintFailure, sprintFailureKindOf } from './sprint-failure';

describe('sprintFailureKindOf', () => {
  it('keeps the kind of a sprint failure', () => {
    expect(sprintFailureKindOf(new SprintFailure('ends_before_start'))).toBe('ends_before_start');
    expect(sprintFailureKindOf(new SprintFailure('active_sprint_exists'))).toBe(
      'active_sprint_exists',
    );
    expect(sprintFailureKindOf(new SprintFailure('forbidden'))).toBe('forbidden');
  });

  it('treats any other error as the service being unavailable', () => {
    expect(sprintFailureKindOf(new Error('boom'))).toBe('unavailable');
    expect(sprintFailureKindOf(undefined)).toBe('unavailable');
  });

  it('names the failure after its kind', () => {
    const failure = new SprintFailure('participant_not_a_member');

    expect(failure.name).toBe('SprintFailure');
    expect(failure.message).toBe('Sprint failure: participant_not_a_member');
  });
});
