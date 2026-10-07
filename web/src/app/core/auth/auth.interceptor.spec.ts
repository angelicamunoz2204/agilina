import { DOCUMENT } from '@angular/common';
import { provideHttpClient, withInterceptors, HttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { FakeAuthSession, provideFakeAuthSession } from '@testing/auth';
import { provideTestRuntimeConfig, TEST_RUNTIME_CONFIG } from '@testing/runtime-config';

import { authInterceptor } from './auth.interceptor';

const API = TEST_RUNTIME_CONFIG.apiUrl;

describe('authInterceptor', () => {
  let session: FakeAuthSession;
  let http: HttpClient;
  let backend: HttpTestingController;

  beforeEach(() => {
    session = new FakeAuthSession(true);
    session.token = 'the-token';
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
        provideTestRuntimeConfig(),
        provideFakeAuthSession(session),
        { provide: DOCUMENT, useValue: { location: { pathname: '/teams/a', search: '?x=1' } } },
      ],
    });
    http = TestBed.inject(HttpClient);
    backend = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    backend.verify();
  });

  /** Lets the interceptor's promise settle before the request is looked for. */
  async function settle(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve));
  }

  it('sends the token to the API', async () => {
    http.get(`${API}/v1/teams`).subscribe();
    await settle();

    expect(backend.expectOne(`${API}/v1/teams`).request.headers.get('Authorization')).toBe(
      'Bearer the-token',
    );
  });

  it('never sends it anywhere else', async () => {
    http.get('http://auth.test/realms/agilina/protocol/openid-connect/certs').subscribe();
    http.get(`${API}.evil.test/v1/teams`).subscribe();
    await settle();

    for (const request of backend.match(() => true)) {
      expect(request.request.headers.has('Authorization')).toBeFalse();
    }
  });

  it('sends no header when nobody is signed in', async () => {
    session.token = null;

    http.get(`${API}/v1/invitations/status`).subscribe();
    await settle();

    expect(
      backend.expectOne(`${API}/v1/invitations/status`).request.headers.has('Authorization'),
    ).toBeFalse();
  });

  it('takes the person to sign in, back to where they were, when the API answers 401', async () => {
    let failed = false;
    http.get(`${API}/v1/teams`).subscribe({ error: () => (failed = true) });
    await settle();

    backend
      .expectOne(`${API}/v1/teams`)
      .flush({ code: 'not_authenticated' }, { status: 401, statusText: 'Unauthorized' });
    await settle();

    expect(failed).toBeTrue();
    expect(session.signIns).toEqual([{ returnUrl: '/teams/a?x=1' }]);
  });

  it('does not sign in again for other errors', async () => {
    http.get(`${API}/v1/teams`).subscribe({ error: () => undefined });
    await settle();

    backend.expectOne(`${API}/v1/teams`).flush({}, { status: 403, statusText: 'Forbidden' });
    await settle();

    expect(session.signIns).toEqual([]);
  });
});
