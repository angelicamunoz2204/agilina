import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../../environments/environment';
import { HttpHealthApi } from './http-health.api';

describe('HttpHealthApi', () => {
  let api: HttpHealthApi;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [HttpHealthApi, provideHttpClient(), provideHttpClientTesting()],
    });
    api = TestBed.inject(HttpHealthApi);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('queries the liveness probe of the API', () => {
    let received: string | undefined;
    api.check().subscribe((status) => (received = status.status));

    const request = http.expectOne(`${environment.apiUrl}/health`);
    expect(request.request.method).toBe('GET');
    request.flush({
      service: 'agilina-api',
      version: '0.1.0',
      environment: 'local',
      status: 'alive',
    });

    expect(received).toBe('alive');
  });
});
