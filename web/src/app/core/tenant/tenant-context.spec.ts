import { TestBed } from '@angular/core/testing';

import { TenantContext } from './tenant-context';

describe('TenantContext', () => {
  let tenant: TenantContext;

  beforeEach(() => {
    tenant = TestBed.inject(TenantContext);
  });

  it('knows no tenant until the address names one', () => {
    expect(tenant.current()).toBeNull();
    expect(() => tenant.require()).toThrowError(/No tenant/);
  });

  it('is the tenant of the address once it is set', () => {
    tenant.set('ecomoda');

    expect(tenant.current()).toBe('ecomoda');
    expect(tenant.require()).toBe('ecomoda');
  });

  it('builds the paths of the tenant, to navigate and to link', () => {
    tenant.set('acme');

    expect(tenant.path('teams', 'abc')).toEqual(['/', 'acme', 'teams', 'abc']);
    expect(tenant.path()).toEqual(['/', 'acme']);
  });

  it('builds the addresses of the tenant', () => {
    tenant.set('acme');

    expect(tenant.url('teams')).toBe('/acme/teams');
    expect(tenant.url('teams', 'new')).toBe('/acme/teams/new');
  });
});
