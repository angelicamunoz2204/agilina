import { Injectable, signal } from '@angular/core';

/**
 * The tenant the application is being used in (AD-29): the organization whose login, database
 * and teams everything on the screen belongs to. It is the first segment of the address
 * (`/acme/teams`) and is set by the route guard before anything asks for it.
 */
@Injectable({ providedIn: 'root' })
export class TenantContext {
  private readonly slug = signal<string | null>(null);

  readonly current = this.slug.asReadonly();

  set(slug: string): void {
    this.slug.set(slug);
  }

  /** The tenant, for what cannot work without one (the sign-in, a call to the API). */
  require(): string {
    const slug = this.slug();
    if (slug === null) {
      throw new Error('No tenant: the address does not name one');
    }
    return slug;
  }

  /** A path inside the tenant, for `routerLink` and `navigate`: `path('teams', id)`. */
  path(...segments: string[]): string[] {
    return ['/', this.require(), ...segments];
  }

  /** The same, as an address: `url('teams')` is `/acme/teams`. */
  url(...segments: string[]): string {
    return `/${[this.require(), ...segments].join('/')}`;
  }
}
