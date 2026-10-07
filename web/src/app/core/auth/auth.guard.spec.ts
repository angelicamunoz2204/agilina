import { TestBed } from '@angular/core/testing';
import {
  type ActivatedRouteSnapshot,
  type CanActivateFn,
  type RouterStateSnapshot,
  UrlTree,
} from '@angular/router';

import { FakeAuthSession, provideFakeAuthSession } from '@testing/auth';
import { provideTestTenant } from '@testing/tenant';

import { authGuard, entranceGuard } from './auth.guard';

function run(guard: CanActivateFn, url = '/acme/teams/a'): Promise<unknown> {
  return TestBed.runInInjectionContext(async () =>
    guard({} as ActivatedRouteSnapshot, { url } as RouterStateSnapshot),
  );
}

describe('authGuard', () => {
  it('lets a signed-in person through', async () => {
    TestBed.configureTestingModule({
      providers: [provideFakeAuthSession(new FakeAuthSession(true)), provideTestTenant()],
    });

    expect(await run(authGuard)).toBeTrue();
  });

  it('stops the others and asks to sign in, back to the page they asked for', async () => {
    const session = new FakeAuthSession(false);
    TestBed.configureTestingModule({
      providers: [provideFakeAuthSession(session), provideTestTenant()],
    });

    expect(await run(authGuard, '/acme/teams/b')).toBeFalse();
    expect(session.ensured).toEqual(['/acme/teams/b']);
  });
});

describe('entranceGuard', () => {
  it('sends a signed-in person to the teams of their tenant', async () => {
    TestBed.configureTestingModule({
      providers: [provideFakeAuthSession(new FakeAuthSession(true)), provideTestTenant()],
    });

    const result = await run(entranceGuard, '/acme');

    expect(result).toBeInstanceOf(UrlTree);
    expect((result as UrlTree).toString()).toBe('/acme/teams');
  });

  it('asks the others to sign in and to land on their teams afterwards', async () => {
    const session = new FakeAuthSession(false);
    TestBed.configureTestingModule({
      providers: [provideFakeAuthSession(session), provideTestTenant()],
    });

    expect(await run(entranceGuard, '/acme')).toBeFalse();
    expect(session.ensured).toEqual(['/acme/teams']);
  });
});
