/**
 * Everything that can go wrong with a team, in the terms of the product and not of HTTP.
 * The adapter translates the API's answers into these.
 */
export type TeamFailureKind = 'not_authenticated' | 'invalid_name' | 'not_a_member' | 'unavailable';

export class TeamFailure extends Error {
  override readonly name = 'TeamFailure';

  constructor(readonly kind: TeamFailureKind) {
    super(`Team failure: ${kind}`);
  }
}

/** What went wrong, for any error that reached a screen: anything unexpected is `unavailable`. */
export function failureKindOf(error: unknown): TeamFailureKind {
  return error instanceof TeamFailure ? error.kind : 'unavailable';
}
