import { TestBed } from '@angular/core/testing';
import {
  type ActivatedRouteSnapshot,
  type CanActivateFn,
  type RouterStateSnapshot,
  UrlTree,
} from '@angular/router';

import { FakeAuthSession, provideFakeAuthSession } from '@testing/auth';

import { authGuard, entranceGuard } from './auth.guard';

function run(guard: CanActivateFn, url = '/teams/a'): Promise<unknown> {
  return TestBed.runInInjectionContext(async () =>
    guard({} as ActivatedRouteSnapshot, { url } as RouterStateSnapshot),
  );
}

describe('authGuard', () => {
  it('lets a signed-in person through', async () => {
    TestBed.configureTestingModule({
      providers: [provideFakeAuthSession(new FakeAuthSession(true))],
    });

    expect(await run(authGuard)).toBeTrue();
  });

  it('stops the others and asks to sign in, back to the page they asked for', async () => {
    const session = new FakeAuthSession(false);
    TestBed.configureTestingModule({ providers: [provideFakeAuthSession(session)] });

    expect(await run(authGuard, '/teams/b')).toBeFalse();
    expect(session.ensured).toEqual(['/teams/b']);
  });
});

describe('entranceGuard', () => {
  it('sends a signed-in person to their teams', async () => {
    TestBed.configureTestingModule({
      providers: [provideFakeAuthSession(new FakeAuthSession(true))],
    });

    const result = await run(entranceGuard, '/');

    expect(result).toBeInstanceOf(UrlTree);
    expect((result as UrlTree).toString()).toBe('/teams');
  });

  it('asks the others to sign in and to land on their teams afterwards', async () => {
    const session = new FakeAuthSession(false);
    TestBed.configureTestingModule({ providers: [provideFakeAuthSession(session)] });

    expect(await run(entranceGuard, '/')).toBeFalse();
    expect(session.ensured).toEqual(['/teams']);
  });
});
