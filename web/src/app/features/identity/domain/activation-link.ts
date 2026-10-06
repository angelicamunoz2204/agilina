const TOKEN_PARAMETER = 't';

/**
 * The activation token travels in the URL fragment (`/activate#t=<token>`): a fragment is
 * never sent to a server or in a Referer header. Returns `null` when there is none.
 */
export function readActivationToken(fragment: string | null): string | null {
  if (fragment === null) {
    return null;
  }
  const token = new URLSearchParams(fragment).get(TOKEN_PARAMETER)?.trim();
  return token === undefined || token === '' ? null : token;
}
