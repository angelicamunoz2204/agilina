import { DOCUMENT } from '@angular/common';
import { TestBed } from '@angular/core/testing';
import { TranslocoService } from '@jsverse/transloco';

import { provideTestI18n } from '@testing/i18n';

import { KEYCLOAK_CLIENT, KeycloakAuthSession, type KeycloakClient } from './keycloak-auth-session';

/** keycloak-js double: records what the adapter asks of it. */
class FakeKeycloak {
  authenticated: boolean | undefined = false;
  token: string | undefined;
  readonly inits: object[] = [];
  readonly logins: object[] = [];
  readonly renewals: number[] = [];
  renewalFails = false;

  init(options: object): Promise<boolean> {
    this.inits.push(options);
    return Promise.resolve(this.authenticated === true);
  }

  login(options: object): Promise<void> {
    this.logins.push(options);
    return Promise.resolve();
  }

  updateToken(minValidity: number): Promise<boolean> {
    this.renewals.push(minValidity);
    return this.renewalFails ? Promise.reject(new Error('session ended')) : Promise.resolve(true);
  }
}

describe('KeycloakAuthSession', () => {
  let keycloak: FakeKeycloak;
  let session: KeycloakAuthSession;

  beforeEach(() => {
    keycloak = new FakeKeycloak();
    TestBed.configureTestingModule({
      providers: [
        KeycloakAuthSession,
        provideTestI18n(),
        { provide: KEYCLOAK_CLIENT, useValue: keycloak as unknown as KeycloakClient },
        {
          provide: DOCUMENT,
          useValue: { location: { href: 'http://app.test/teams/a', origin: 'http://app.test' } },
        },
      ],
    });
    session = TestBed.inject(KeycloakAuthSession);
  });

  it('starts keycloak-js once, with PKCE and without any redirect of its own', async () => {
    await session.accessToken();
    await session.accessToken();
    await session.ensureSignedIn();

    expect(keycloak.inits).toEqual([{ pkceMethod: 'S256', checkLoginIframe: false }]);
  });

  it('is not signed in until something has asked', () => {
    expect(session.authenticated()).toBeFalse();
  });

  describe('ensureSignedIn', () => {
    it('says yes when there is a session, and records it', async () => {
      keycloak.authenticated = true;

      expect(await session.ensureSignedIn('/teams')).toBeTrue();
      expect(session.authenticated()).toBeTrue();
      expect(keycloak.logins).toEqual([]);
    });

    it('takes the person to sign in, back to the page they were on, in their language', async () => {
      expect(await session.ensureSignedIn()).toBeFalse();

      expect(keycloak.logins).toEqual([{ redirectUri: 'http://app.test/teams/a', locale: 'es' }]);
    });

    it('comes back to the page the guard asked for', async () => {
      await session.ensureSignedIn('/teams/b');

      expect(keycloak.logins).toEqual([{ redirectUri: 'http://app.test/teams/b', locale: 'es' }]);
    });

    it('asks in the language the application is in', async () => {
      TestBed.inject(TranslocoService).setActiveLang('en');

      await session.ensureSignedIn();

      expect(keycloak.logins).toEqual([{ redirectUri: 'http://app.test/teams/a', locale: 'en' }]);
    });
  });

  describe('accessToken', () => {
    it('is null while nobody is signed in', async () => {
      expect(await session.accessToken()).toBeNull();
      expect(keycloak.renewals).toEqual([]);
    });

    it('renews the token when it is about to expire and gives it', async () => {
      keycloak.authenticated = true;
      keycloak.token = 'the-token';

      expect(await session.accessToken()).toBe('the-token');
      expect(keycloak.renewals).toEqual([30]);
    });

    it('signs in again when the session ended and cannot be renewed', async () => {
      keycloak.authenticated = true;
      keycloak.token = 'the-token';
      await session.ensureSignedIn();
      keycloak.renewalFails = true;

      expect(await session.accessToken()).toBeNull();
      expect(session.authenticated()).toBeFalse();
      expect(keycloak.logins).toHaveSize(1);
    });

    it('is null when keycloak-js has no token even though it says there is a session', async () => {
      keycloak.authenticated = true;

      expect(await session.accessToken()).toBeNull();
    });
  });

  describe('signIn', () => {
    it('goes to the sign-in with the email and the page to come back to', async () => {
      await session.signIn({ loginHint: 'julian@example.test', returnUrl: '/teams' });

      expect(keycloak.logins).toEqual([
        { redirectUri: 'http://app.test/teams', locale: 'es', loginHint: 'julian@example.test' },
      ]);
    });

    it('works with no options', async () => {
      await session.signIn();

      expect(keycloak.logins).toEqual([{ redirectUri: 'http://app.test/teams/a', locale: 'es' }]);
    });
  });
});
