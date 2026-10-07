import { ApplicationInitStatus, DOCUMENT } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { Logger } from '@core/logging/logger';
import { FakeLogger } from '@testing/fake-logger';
import { provideTestI18n } from '@testing/i18n';
import { provideTestRuntimeConfig } from '@testing/runtime-config';

import { AuthSession } from './auth-session';
import {
  KEYCLOAK_CLIENT_FACTORY,
  KeycloakAuthSession,
  type KeycloakClient,
} from './keycloak-auth-session';
import { provideAuth } from './provide-auth';

/** keycloak-js double: counts the starts, and can fail to read the answer. */
class FakeKeycloak {
  authenticated = false;
  inits = 0;
  fails = false;

  init(): Promise<boolean> {
    this.inits++;
    if (this.fails) {
      return Promise.reject(new Error('code already used'));
    }
    this.authenticated = true;
    return Promise.resolve(true);
  }
}

describe('provideAuth', () => {
  let keycloak: FakeKeycloak;
  let logger: FakeLogger;
  /** The realms a keycloak-js client was made for. */
  let realms: string[];

  /** Starts the application at this address and waits for its initializers. */
  async function startAt(pathname: string, hash: string): Promise<void> {
    TestBed.configureTestingModule({
      providers: [
        provideTestI18n(),
        provideTestRuntimeConfig(),
        provideAuth(),
        {
          provide: KEYCLOAK_CLIENT_FACTORY,
          useValue: (realm: string): KeycloakClient => {
            realms.push(realm);
            return keycloak as unknown as KeycloakClient;
          },
        },
        { provide: Logger, useValue: logger },
        {
          provide: DOCUMENT,
          useValue: { location: { href: `http://app.test${pathname}${hash}`, pathname, hash } },
        },
      ],
    });
    await TestBed.inject(ApplicationInitStatus).donePromise;
  }

  beforeEach(() => {
    keycloak = new FakeKeycloak();
    logger = new FakeLogger();
    realms = [];
  });

  it("reads Keycloak's answer while the application starts, before any navigation", async () => {
    await startAt('/acme/teams/a', '#state=s-1&session_state=x&code=c-1');

    expect(realms).toEqual(['agilina-acme']);
    expect(keycloak.inits).toBe(1);
    expect(TestBed.inject(AuthSession).authenticated()).toBeTrue();
  });

  it('serves one session to the whole application', async () => {
    await startAt('/acme/teams', '');

    expect(TestBed.inject(AuthSession)).toBe(TestBed.inject(KeycloakAuthSession));
  });

  it('starts nothing when the address carries no answer', async () => {
    await startAt('/acme/activate', '#t=activation-token');

    expect(keycloak.inits).toBe(0);
  });

  it('logs an answer that cannot be read and lets the application start', async () => {
    keycloak.fails = true;

    await startAt('/acme/teams/a', '#state=s-1&code=c-1');

    expect(logger.entries).toEqual([
      jasmine.objectContaining({
        level: 'error',
        message: 'The answer of the sign-in could not be read',
      }),
    ]);
  });
});
