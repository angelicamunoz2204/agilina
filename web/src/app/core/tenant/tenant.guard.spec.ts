import { TestBed } from '@angular/core/testing';
import {
  type ActivatedRouteSnapshot,
  convertToParamMap,
  type RouterStateSnapshot,
  UrlSegment,
  UrlTree,
} from '@angular/router';

import { FakeTenantPort, provideFakeTenantPort } from '@testing/tenant';

import { TenantContext } from './tenant-context';
import { tenantGuard, tenantMatch } from './tenant.guard';

/** The router also hands the matcher the snapshot so far; this one does not use it. */
type Matcher = (route: object, segments: UrlSegment[]) => boolean;

function matches(...paths: string[]): boolean {
  const segments = paths.map((path) => new UrlSegment(path, {}));
  return (tenantMatch as unknown as Matcher)({}, segments);
}

function activate(tenant: string | null): Promise<unknown> {
  const route = { paramMap: convertToParamMap(tenant === null ? {} : { tenant }) };
  return TestBed.runInInjectionContext(
    async () =>
      await tenantGuard(route as ActivatedRouteSnapshot, { url: '/acme' } as RouterStateSnapshot),
  );
}

describe('tenantMatch', () => {
  it('opens the routes of a tenant for an address that can be one', () => {
    expect(matches('acme', 'teams')).toBeTrue();
    expect(matches('ecomoda')).toBeTrue();
  });

  it('leaves everything else to the page that is not found', () => {
    expect(matches()).toBeFalse();
    expect(matches('Acme')).toBeFalse();
    expect(matches('ac-me')).toBeFalse();
    expect(matches('platform')).toBeFalse();
    expect(matches('not-found')).toBeFalse();
  });
});

describe('tenantGuard', () => {
  let tenants: FakeTenantPort;

  beforeEach(() => {
    tenants = new FakeTenantPort();
    TestBed.configureTestingModule({ providers: [provideFakeTenantPort(tenants)] });
  });

  it('records the tenant of the address and lets through an organization that exists', async () => {
    expect(await activate('ecomoda')).toBeTrue();

    expect(TestBed.inject(TenantContext).current()).toBe('ecomoda');
    expect(tenants.asked).toEqual(['ecomoda']);
  });

  it('sends a name that looks right but belongs to nobody to the page that is not found', async () => {
    const result = await activate('nobody');

    expect(result).toBeInstanceOf(UrlTree);
    expect((result as UrlTree).toString()).toBe('/not-found');
  });

  it('lets the person go on when the platform cannot be asked: the screen will say so', async () => {
    tenants.failure = new Error('503');

    expect(await activate('acme')).toBeTrue();
  });

  it('stops an address with no tenant in it, without asking anybody', async () => {
    expect(await activate(null)).toBeFalse();

    expect(tenants.asked).toEqual([]);
    expect(TestBed.inject(TenantContext).current()).toBeNull();
  });
});
