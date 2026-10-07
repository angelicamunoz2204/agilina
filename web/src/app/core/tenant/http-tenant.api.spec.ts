import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { WITHOUT_SESSION } from '@core/auth/auth.interceptor';
import { provideTestRuntimeConfig, TEST_RUNTIME_CONFIG } from '@testing/runtime-config';

import { HttpTenantApi } from './http-tenant.api';
import { TenantNotFoundError } from './tenant-not-found-error';
import { type TenantInfo } from './tenant.port';

describe('HttpTenantApi', () => {
  let api: HttpTenantApi;
  let backend: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        HttpTenantApi,
        provideHttpClient(),
        provideHttpClientTesting(),
        provideTestRuntimeConfig(),
      ],
    });
    api = TestBed.inject(HttpTenantApi);
    backend = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    backend.verify();
  });

  it('asks the platform for the tenant, without a session, and maps the answer', () => {
    let received: TenantInfo | undefined;
    api.find('ecomoda').subscribe((tenant) => (received = tenant));

    const request = backend.expectOne(`${TEST_RUNTIME_CONFIG.apiUrl}/v1/tenant`);
    expect(request.request.method).toBe('GET');
    expect(request.request.context.get(WITHOUT_SESSION)).toBeTrue();
    request.flush({ slug: 'ecomoda', display_name: 'Ecomoda', language: 'es' });

    expect(received).toEqual({ slug: 'ecomoda', displayName: 'Ecomoda', language: 'es' });
  });

  it('says the tenant is not there when the platform answers 404', () => {
    let failure: unknown;
    api.find('nobody').subscribe({ error: (error: unknown) => (failure = error) });

    backend
      .expectOne(`${TEST_RUNTIME_CONFIG.apiUrl}/v1/tenant`)
      .flush({ error: { code: 'tenant_not_found' } }, { status: 404, statusText: 'Not Found' });

    expect(failure).toBeInstanceOf(TenantNotFoundError);
  });

  it('passes on any other failure as it is: the platform could not be asked', () => {
    let failure: unknown;
    api.find('acme').subscribe({ error: (error: unknown) => (failure = error) });

    backend
      .expectOne(`${TEST_RUNTIME_CONFIG.apiUrl}/v1/tenant`)
      .flush({}, { status: 503, statusText: 'Service Unavailable' });

    expect(failure).not.toBeInstanceOf(TenantNotFoundError);
    expect(failure).toBeTruthy();
  });
});
