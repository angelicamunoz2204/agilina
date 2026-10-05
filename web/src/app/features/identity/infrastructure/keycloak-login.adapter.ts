import { DOCUMENT } from '@angular/common';
import { inject, Injectable } from '@angular/core';

import { RUNTIME_CONFIG } from '@core/config/runtime-config';

import { buildKeycloakLoginUrl } from './keycloak-login-url';
import { createPkce, randomUrlSafe } from './pkce';
import { type LoginRedirectPort } from '../application/login-redirect.port';

/**
 * Sends the person to Keycloak's sign-in page without any library.
 *
 * It only starts the flow. Keycloak returns to the application with an authorization code
 * that nothing exchanges yet, so no session starts: the sign-in story (HU-03) replaces
 * this adapter with the one that completes it. The PKCE verifier is therefore not kept.
 */
@Injectable()
export class KeycloakLoginAdapter implements LoginRedirectPort {
  private readonly keycloak = inject(RUNTIME_CONFIG).keycloak;
  private readonly document = inject(DOCUMENT);

  async redirect(loginHint?: string): Promise<void> {
    const { challenge } = await createPkce();
    const url = buildKeycloakLoginUrl({
      keycloakUrl: this.keycloak.url,
      realm: this.keycloak.realm,
      clientId: this.keycloak.clientId,
      redirectUri: `${this.document.location.origin}/`,
      state: randomUrlSafe(16),
      codeChallenge: challenge,
      ...(loginHint !== undefined && { loginHint }),
    });
    this.document.location.assign(url);
  }
}
