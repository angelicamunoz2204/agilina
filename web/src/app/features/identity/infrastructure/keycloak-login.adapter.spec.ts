import { DOCUMENT } from '@angular/common';
import { TestBed } from '@angular/core/testing';

import { provideTestRuntimeConfig } from '@testing/runtime-config';

import { KeycloakLoginAdapter } from './keycloak-login.adapter';

describe('KeycloakLoginAdapter', () => {
  const visited: string[] = [];
  let adapter: KeycloakLoginAdapter;

  beforeEach(() => {
    visited.length = 0;
    TestBed.configureTestingModule({
      providers: [
        KeycloakLoginAdapter,
        provideTestRuntimeConfig(),
        {
          provide: DOCUMENT,
          useValue: {
            location: { origin: 'http://app.test', assign: (url: string) => visited.push(url) },
          },
        },
      ],
    });
    adapter = TestBed.inject(KeycloakLoginAdapter);
  });

  it('sends the person to the sign-in of the realm with their email filled in', async () => {
    await adapter.redirect('julian@example.test');

    expect(visited).toHaveSize(1);
    const url = new URL(visited[0] ?? '');
    expect(url.origin).toBe('http://auth.test');
    expect(url.pathname).toBe('/realms/agilina/protocol/openid-connect/auth');
    expect(url.searchParams.get('client_id')).toBe('agilina-web');
    expect(url.searchParams.get('redirect_uri')).toBe('http://app.test/');
    expect(url.searchParams.get('login_hint')).toBe('julian@example.test');
    expect(url.searchParams.get('code_challenge_method')).toBe('S256');
    expect(url.searchParams.get('code_challenge')).toMatch(/^[A-Za-z0-9_-]{43}$/);
    expect(url.searchParams.get('state')).toBeTruthy();
  });

  it('can also send them without knowing their email', async () => {
    await adapter.redirect();

    expect(new URL(visited[0] ?? '').searchParams.has('login_hint')).toBeFalse();
  });
});
