import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { provideTestRuntimeConfig, TEST_RUNTIME_CONFIG } from '@testing/runtime-config';

import { HttpHealthApi } from './http-health.api';
import { type ServiceStatus } from '../domain/service-status';

describe('HttpHealthApi', () => {
  let api: HttpHealthApi;
  let backend: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        HttpHealthApi,
        provideHttpClient(),
        provideHttpClientTesting(),
        provideTestRuntimeConfig(),
      ],
    });
    api = TestBed.inject(HttpHealthApi);
    backend = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    backend.verify();
  });

  it('queries the liveness probe of the API and maps it to the domain', () => {
    let received: ServiceStatus | undefined;
    api.check().subscribe((status) => (received = status));

    const request = backend.expectOne(`${TEST_RUNTIME_CONFIG.apiUrl}/health`);
    expect(request.request.method).toBe('GET');
    request.flush({
      service: 'agilina-api',
      version: '0.1.0',
      environment: 'local',
      status: 'alive',
    });

    expect(received).toEqual({
      service: 'agilina-api',
      version: '0.1.0',
      environment: 'local',
      status: 'alive',
    });
  });
});
