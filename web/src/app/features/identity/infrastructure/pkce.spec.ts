import { createPkce, randomUrlSafe } from './pkce';

describe('PKCE', () => {
  it('makes random strings that are safe in a URL and different every time', () => {
    const first = randomUrlSafe(32);

    expect(first).toMatch(/^[A-Za-z0-9_-]{43}$/);
    expect(randomUrlSafe(32)).not.toBe(first);
  });

  it('derives the challenge from the verifier with SHA-256, base64url encoded', async () => {
    const { verifier, challenge } = await createPkce();

    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier));
    const expected = btoa(String.fromCharCode(...new Uint8Array(digest)))
      .replaceAll('+', '-')
      .replaceAll('/', '_')
      .replaceAll('=', '');
    expect(challenge).toBe(expected);
    expect(challenge).not.toBe(verifier);
  });
});
