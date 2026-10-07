import { DOCUMENT } from '@angular/common';
import { inject, Injectable, InjectionToken, signal } from '@angular/core';
import { TranslocoService } from '@jsverse/transloco';
import type Keycloak from 'keycloak-js';

import { type AuthSession, type SignInOptions } from './auth-session';

/** The part of keycloak-js this adapter uses: what a test double has to answer. */
export type KeycloakClient = Pick<
  Keycloak,
  'init' | 'login' | 'updateToken' | 'authenticated' | 'token'
>;

/** The configured keycloak-js client, built in provide-auth.ts. */
export const KEYCLOAK_CLIENT = new InjectionToken<KeycloakClient>('KEYCLOAK_CLIENT');

/** The access token is renewed when it has less than this many seconds left. */
const MIN_TOKEN_VALIDITY_SECONDS = 30;

/**
 * Whether the fragment of the address is Keycloak's answer to a sign-in (`#state=…&code=…`,
 * or `#state=…&error=…`). The activation link (`#t=…`) is not.
 */
export function isSignInAnswer(fragment: string): boolean {
  const params = new URLSearchParams(fragment.replace(/^#/, ''));
  return params.has('state') && (params.has('code') || params.has('error'));
}

/**
 * Keycloak adapter of the session (authorization code flow with PKCE, which the realm's
 * `agilina-web` client requires). The tokens live in memory only: never in localStorage.
 */
@Injectable()
export class KeycloakAuthSession implements AuthSession {
  private readonly keycloak = inject(KEYCLOAK_CLIENT);
  private readonly document = inject(DOCUMENT);
  private readonly language = inject(TranslocoService);
  private readonly signedIn = signal(false);
  private started: Promise<void> | null = null;

  readonly authenticated = this.signedIn.asReadonly();

  async ensureSignedIn(returnUrl?: string): Promise<boolean> {
    await this.start();
    if (this.keycloak.authenticated) {
      return true;
    }
    await this.redirectToSignIn(returnUrl === undefined ? {} : { returnUrl });
    return false;
  }

  async accessToken(): Promise<string | null> {
    await this.start();
    if (!this.keycloak.authenticated) {
      return null;
    }
    try {
      await this.keycloak.updateToken(MIN_TOKEN_VALIDITY_SECONDS);
    } catch {
      // The session cannot be renewed (it ended in Keycloak): sign in again.
      this.signedIn.set(false);
      await this.redirectToSignIn({});
      return null;
    }
    return this.keycloak.token ?? null;
  }

  async signIn(options: SignInOptions = {}): Promise<void> {
    await this.start();
    await this.redirectToSignIn(options);
  }

  /**
   * Reads Keycloak's answer to a sign-in that has just come back, when the address carries
   * one, so that it happens before the router reads the address (provide-auth.ts runs it while
   * the application starts). keycloak-js takes the answer out of the address; read later, from
   * the guard, the router would write the address it started with back, answer included.
   * Without an answer it does nothing: the public screens never start keycloak-js.
   */
  async readSignInAnswer(): Promise<void> {
    if (isSignInAnswer(this.document.location.hash)) {
      await this.start();
    }
  }

  /**
   * Starts keycloak-js once. With no `onLoad` it only reads the answer of a sign-in that
   * has just come back (the `code` in the address) and redirects nowhere.
   */
  private start(): Promise<void> {
    this.started ??= this.keycloak
      .init({ pkceMethod: 'S256', checkLoginIframe: false })
      .then(() => {
        this.signedIn.set(this.keycloak.authenticated);
      });
    return this.started;
  }

  private async redirectToSignIn(options: SignInOptions): Promise<void> {
    const location = this.document.location;
    const returnUrl = options.returnUrl;
    await this.keycloak.login({
      redirectUri: returnUrl === undefined ? location.href : `${location.origin}${returnUrl}`,
      locale: this.language.getActiveLang(),
      ...(options.loginHint !== undefined && { loginHint: options.loginHint }),
    });
  }
}
