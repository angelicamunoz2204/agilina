/**
 * Everything that can go wrong with the sprint of a team, in the terms of the product and not
 * of HTTP. The adapter translates the API's answers into these.
 */
export type SprintFailureKind =
  | 'not_authenticated'
  | 'forbidden'
  | 'no_active_sprint'
  | 'active_sprint_exists'
  | 'ends_before_start'
  | 'invalid_time_zone'
  | 'no_participants'
  | 'duplicate_participant'
  | 'participant_not_a_member'
  | 'unavailable';

export class SprintFailure extends Error {
  override readonly name = 'SprintFailure';

  constructor(readonly kind: SprintFailureKind) {
    super(`Sprint failure: ${kind}`);
  }
}

/** What went wrong, for any error that reached a screen: anything unexpected is `unavailable`. */
export function sprintFailureKindOf(error: unknown): SprintFailureKind {
  return error instanceof SprintFailure ? error.kind : 'unavailable';
}
