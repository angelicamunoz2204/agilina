import { DOCUMENT } from '@angular/common';
import { TestBed } from '@angular/core/testing';
import { TranslocoService } from '@jsverse/transloco';

import { provideTestI18n } from '@testing/i18n';

import {
  isSignInAnswer,
  KEYCLOAK_CLIENT,
  KeycloakAuthSession,
  type KeycloakClient,
} from './keycloak-auth-session';

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
          useValue: {
            location: { href: 'http://app.test/teams/a', origin: 'http://app.test', hash: '' },
          },
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

  describe('readSignInAnswer', () => {
    function arriveWith(hash: string): void {
      (TestBed.inject(DOCUMENT).location as { hash: string }).hash = hash;
    }

    it("reads Keycloak's answer right away when the address carries one", async () => {
      keycloak.authenticated = true;
      arriveWith('#state=s-1&session_state=x&iss=http%3A%2F%2Fkc&code=c-1');

      await session.readSignInAnswer();

      expect(keycloak.inits).toEqual([{ pkceMethod: 'S256', checkLoginIframe: false }]);
      expect(session.authenticated()).toBeTrue();
    });

    it('starts keycloak-js only once: the guard that asks later reuses that start', async () => {
      keycloak.authenticated = true;
      arriveWith('#state=s-1&code=c-1');

      await session.readSignInAnswer();
      expect(await session.ensureSignedIn('/teams/a')).toBeTrue();

      expect(keycloak.inits.length).toBe(1);
      expect(keycloak.logins).toEqual([]);
    });

    it('does nothing on a page without an answer, such as the activation link', async () => {
      arriveWith('#t=activation-token');
      await session.readSignInAnswer();
      arriveWith('');
      await session.readSignInAnswer();

      expect(keycloak.inits).toEqual([]);
    });
  });

  describe('isSignInAnswer', () => {
    it('recognises a code or an error that comes with its state', () => {
      expect(isSignInAnswer('#state=s&code=c')).toBeTrue();
      expect(isSignInAnswer('#state=s&error=access_denied')).toBeTrue();
      expect(isSignInAnswer('state=s&code=c')).toBeTrue();
    });

    it('ignores anything else', () => {
      expect(isSignInAnswer('')).toBeFalse();
      expect(isSignInAnswer('#t=token')).toBeFalse();
      expect(isSignInAnswer('#code=c')).toBeFalse();
      expect(isSignInAnswer('#state=s')).toBeFalse();
    });
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
