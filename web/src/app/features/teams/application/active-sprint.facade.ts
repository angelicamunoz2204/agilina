import { computed, inject, Injectable, signal, type Signal } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';

import { SprintsPort } from './sprints.port';
import { type ActiveSprint } from '../domain/active-sprint';

/**
 * The active sprint of the team whose id the page receives, for the dashboard's "day N of M"
 * line. Provided by the page, so it lives and dies with it.
 *
 * A failed request leaves the sprint unknown and the line hidden: the dashboard still shows the
 * team. The HTTP interceptor has already logged it, so it is not logged again here.
 */
@Injectable()
export class ActiveSprintFacade {
  private readonly port = inject(SprintsPort);
  private readonly teamId = signal<Signal<string> | null>(null);
  private readonly current = rxResource({
    params: () => this.teamId()?.(),
    stream: ({ params }) => this.port.active(params),
  });

  /** Whether the API already answered: until then, and if it failed, there is nothing to say. */
  readonly known = computed(() => this.current.hasValue());
  /** The active sprint, or null when the team has none (or the API has not answered). */
  readonly sprint = computed<ActiveSprint | null>(() =>
    this.current.hasValue() ? this.current.value() : null,
  );

  /** Loads the sprint of the team of this id, and loads it again whenever the id changes. */
  follow(teamId: Signal<string>): void {
    this.teamId.set(teamId);
  }
}
