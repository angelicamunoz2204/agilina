/** Why the Keycloak password policy refused a password; the API reports them as stable codes. */
export type PasswordRejection = 'min_length' | 'not_username' | 'not_email' | 'other';

/**
 * Everything that can go wrong with an invitation, in the terms of the product and not of
 * HTTP. The adapter translates the API's answers into these.
 */
export type InvitationFailureKind =
  | 'not_found'
  | 'used'
  | 'expired'
  | 'revoked'
  | 'account_exists'
  | 'password_rejected'
  | 'password_mismatch'
  | 'still_valid'
  | 'no_admins'
  | 'unavailable';

export class InvitationFailure extends Error {
  override readonly name = 'InvitationFailure';

  constructor(
    readonly kind: InvitationFailureKind,
    /** Only for `password_rejected`: which rules the password broke. */
    readonly reasons: readonly PasswordRejection[] = [],
  ) {
    super(`Invitation failure: ${kind}`);
  }
}
