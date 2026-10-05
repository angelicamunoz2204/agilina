import { buildKeycloakLoginUrl } from './keycloak-login-url';

const PARAMS = {
  keycloakUrl: 'http://auth.test',
  realm: 'agilina',
  clientId: 'agilina-web',
  redirectUri: 'http://app.test/',
  state: 'the-state',
  codeChallenge: 'the-challenge',
};

describe('buildKeycloakLoginUrl', () => {
  it('points to the authorization endpoint of the realm', () => {
    const url = new URL(buildKeycloakLoginUrl(PARAMS));

    expect(`${url.origin}${url.pathname}`).toBe(
      'http://auth.test/realms/agilina/protocol/openid-connect/auth',
    );
  });

  it('asks for the authorization code flow with PKCE for the web client', () => {
    const query = new URL(buildKeycloakLoginUrl(PARAMS)).searchParams;

    expect(Object.fromEntries(query)).toEqual({
      client_id: 'agilina-web',
      redirect_uri: 'http://app.test/',
      response_type: 'code',
      scope: 'openid',
      state: 'the-state',
      code_challenge: 'the-challenge',
      code_challenge_method: 'S256',
    });
  });

  it('fills in the email so that the person only types the password', () => {
    const query = new URL(
      buildKeycloakLoginUrl({ ...PARAMS, loginHint: 'julian+team@example.test' }),
    ).searchParams;

    expect(query.get('login_hint')).toBe('julian+team@example.test');
  });

  it('leaves the hint out when there is no email', () => {
    expect(new URL(buildKeycloakLoginUrl(PARAMS)).searchParams.has('login_hint')).toBeFalse();
    expect(
      new URL(buildKeycloakLoginUrl({ ...PARAMS, loginHint: '' })).searchParams.has('login_hint'),
    ).toBeFalse();
  });
});
