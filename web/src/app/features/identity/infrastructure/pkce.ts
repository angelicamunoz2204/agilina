/** A random string safe to put in a URL (base64url, no padding). */
export function randomUrlSafe(byteCount: number): string {
  return base64Url(crypto.getRandomValues(new Uint8Array(byteCount)));
}

/** The PKCE pair: a secret `verifier` and the `challenge` (its SHA-256) that is sent first. */
export async function createPkce(): Promise<{ verifier: string; challenge: string }> {
  const verifier = randomUrlSafe(32);
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
  return { verifier, challenge: base64Url(new Uint8Array(digest)) };
}

function base64Url(bytes: Uint8Array): string {
  const binary = Array.from(bytes, (byte) => String.fromCharCode(byte)).join('');
  return btoa(binary).replaceAll('+', '-').replaceAll('/', '_').replaceAll('=', '');
}
