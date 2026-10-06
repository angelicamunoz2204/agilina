/**
 * Everything that can go wrong with the members of a team, in the terms of the product and
 * not of HTTP. The adapter translates the API's answers into these.
 */
export type MemberFailureKind =
  | 'not_authenticated'
  | 'forbidden'
  | 'not_found'
  | 'already_member'
  | 'account_disabled'
  | 'invalid_email'
  | 'invalid_name'
  | 'last_admin'
  | 'sprint_in_progress'
  | 'mail_unavailable'
  | 'unavailable';

export class MemberFailure extends Error {
  override readonly name = 'MemberFailure';

  constructor(readonly kind: MemberFailureKind) {
    super(`Member failure: ${kind}`);
  }
}

/** What went wrong, for any error that reached a screen: anything unexpected is `unavailable`. */
export function memberFailureKindOf(error: unknown): MemberFailureKind {
  return error instanceof MemberFailure ? error.kind : 'unavailable';
}
