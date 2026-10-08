import { computed, inject, Injectable, signal } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';

import { UsersPort } from './users.port';
import { memberFailureKindOf, type MemberFailureKind } from '../domain/member-failure';
import { type TeamMember } from '../domain/team-member';

/**
 * State of the detail of one user of a team: the API is asked for them each time the dialog
 * opens, so what it shows is never older than the click. Provided by the dialog, so it lives
 * and dies with it.
 */
@Injectable()
export class UserDetailFacade {
  private readonly port = inject(UsersPort);
  private readonly target = signal<{ teamId: string; userId: string } | null>(null);
  private readonly current = rxResource({
    params: () => this.target() ?? undefined,
    stream: ({ params }) => this.port.get(params.teamId, params.userId),
  });

  readonly user = computed<TeamMember | null>(() =>
    this.current.hasValue() ? this.current.value() : null,
  );
  readonly loading = this.current.isLoading;
  /** What went wrong, when the user could not be read. */
  readonly problem = computed<MemberFailureKind | null>(() =>
    this.current.status() === 'error' ? memberFailureKindOf(this.current.error()) : null,
  );

  follow(teamId: string, userId: string): void {
    this.target.set({ teamId, userId });
  }
}
