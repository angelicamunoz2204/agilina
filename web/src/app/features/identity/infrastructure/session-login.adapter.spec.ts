import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { AuthSession, type SignInOptions } from '@core/auth/auth-session';
import { provideTestTenant } from '@testing/tenant';

import { SessionLoginAdapter } from './session-login.adapter';

class FakeSession extends AuthSession {
  readonly authenticated = signal(false).asReadonly();
  readonly signIns: SignInOptions[] = [];

  ensureSignedIn(): Promise<boolean> {
    return Promise.resolve(false);
  }

  accessToken(): Promise<string | null> {
    return Promise.resolve(null);
  }

  signIn(options: SignInOptions = {}): Promise<void> {
    this.signIns.push(options);
    return Promise.resolve();
  }
}

describe('SessionLoginAdapter', () => {
  let session: FakeSession;
  let adapter: SessionLoginAdapter;

  beforeEach(() => {
    session = new FakeSession();
    TestBed.configureTestingModule({
      providers: [
        SessionLoginAdapter,
        { provide: AuthSession, useValue: session },
        provideTestTenant('ecomoda'),
      ],
    });
    adapter = TestBed.inject(SessionLoginAdapter);
  });

  it('signs in with the email filled in and lands on the teams of the tenant afterwards', async () => {
    await adapter.redirect('julian@example.test');

    expect(session.signIns).toEqual([
      { returnUrl: '/ecomoda/teams', loginHint: 'julian@example.test' },
    ]);
  });

  it('can also sign in without knowing the email', async () => {
    await adapter.redirect();

    expect(session.signIns).toEqual([{ returnUrl: '/ecomoda/teams' }]);
  });
});
