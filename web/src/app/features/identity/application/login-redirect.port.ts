/**
 * Port towards the sign-in. An abstract class so that it doubles as the injection token.
 */
export abstract class LoginRedirectPort {
  /** Takes the person to sign in, with their email already typed when known, and brings
   * them to their teams afterwards. */
  abstract redirect(loginHint?: string): Promise<void>;
}
