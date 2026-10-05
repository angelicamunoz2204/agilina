/**
 * Port towards the sign-in. An abstract class so that it doubles as the injection token.
 */
export abstract class LoginRedirectPort {
  /** Takes the person to the sign-in page, with their email already typed when known. */
  abstract redirect(loginHint?: string): Promise<void>;
}
