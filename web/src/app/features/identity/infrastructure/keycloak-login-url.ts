export interface KeycloakLoginUrlParams {
  /** Base URL of Keycloak, without a trailing slash. */
  readonly keycloakUrl: string;
  readonly realm: string;
  readonly clientId: string;
  readonly redirectUri: string;
  readonly state: string;
  readonly codeChallenge: string;
  readonly loginHint?: string;
}

/**
 * The address of Keycloak's sign-in page (OpenID Connect authorization code flow with
 * PKCE, which the `agilina-web` client requires). `login_hint` fills in the email so that
 * the person only types their password.
 */
export function buildKeycloakLoginUrl(params: KeycloakLoginUrlParams): string {
  const query = new URLSearchParams({
    client_id: params.clientId,
    redirect_uri: params.redirectUri,
    response_type: 'code',
    scope: 'openid',
    state: params.state,
    code_challenge: params.codeChallenge,
    code_challenge_method: 'S256',
  });
  if (params.loginHint !== undefined && params.loginHint !== '') {
    query.set('login_hint', params.loginHint);
  }
  const realm = encodeURIComponent(params.realm);
  return `${params.keycloakUrl}/realms/${realm}/protocol/openid-connect/auth?${query.toString()}`;
}
