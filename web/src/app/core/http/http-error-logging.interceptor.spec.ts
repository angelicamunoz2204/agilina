import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { Logger } from '@core/logging/logger';
import { provideFakeLogger, type FakeLogger } from '@testing/fake-logger';

import { httpErrorLoggingInterceptor } from './http-error-logging.interceptor';

describe('httpErrorLoggingInterceptor', () => {
  let http: HttpClient;
  let backend: HttpTestingController;
  let logger: FakeLogger;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(withInterceptors([httpErrorLoggingInterceptor])),
        provideHttpClientTesting(),
        provideFakeLogger(),
      ],
    });
    http = TestBed.inject(HttpClient);
    backend = TestBed.inject(HttpTestingController);
    logger = TestBed.inject(Logger) as FakeLogger;
  });

  afterEach(() => {
    backend.verify();
  });

  it('logs a failed request and lets the error through', () => {
    let failed = false;
    http.get('/teams?token=secret').subscribe({ error: () => (failed = true) });

    backend.expectOne('/teams?token=secret').flush(null, { status: 503, statusText: 'Down' });

    expect(failed).toBeTrue();
    expect(logger.entries[0]?.context).toEqual({ method: 'GET', url: '/teams', status: 503 });
  });

  it('logs nothing when the request succeeds', () => {
    http.get('/teams').subscribe();

    backend.expectOne('/teams').flush([]);

    expect(logger.entries).toEqual([]);
  });
});
