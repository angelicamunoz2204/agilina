import {
  computed,
  inject,
  Injectable,
  signal,
  type Signal,
  type WritableSignal,
} from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { firstValueFrom, type Observable } from 'rxjs';

import { UsersPort } from './users.port';
import { memberFailureKindOf, type MemberFailureKind } from '../domain/member-failure';
import { type RoleOption, type TeamMember, type TeamRole } from '../domain/team-member';

/**
 * State of the team settings: the members of the team whose id the page receives, and the
 * changes an admin makes on them. Provided by the page, so it lives and dies with it.
 *
 * The list comes again from the API after every change, whether it worked or not: the API
 * decides what can change (the last admin, a sprint in progress), so the screen never guesses.
 * A failed request becomes a problem the screen translates; the HTTP interceptor has already
 * logged it, so it is not logged again here.
 */
@Injectable()
export class TeamMembersFacade {
  private readonly port = inject(UsersPort);
  private readonly teamId = signal<Signal<string> | null>(null);
  private readonly listing = rxResource({
    params: () => this.teamId()?.(),
    stream: ({ params }) => this.port.list(params),
  });
  private readonly busyMember = signal<string | null>(null);
  private readonly lastRoleChangeProblem = signal<MemberFailureKind | null>(null);
  private readonly lastRemovalProblem = signal<MemberFailureKind | null>(null);

  /** Null until the API answers. */
  readonly members = computed<readonly TeamMember[] | null>(() =>
    this.listing.hasValue() ? this.listing.value().members : null,
  );
  readonly roles = computed<readonly RoleOption[]>(() =>
    this.listing.hasValue() ? this.listing.value().roles : [],
  );
  readonly loading = this.listing.isLoading;
  readonly failed = computed(() => this.listing.status() === 'error');
  /** What went wrong, when the list could not be loaded. */
  readonly problem = computed<MemberFailureKind | null>(() =>
    this.failed() ? memberFailureKindOf(this.listing.error()) : null,
  );
  /** The member whose change is being saved, if any. */
  readonly savingMember = this.busyMember.asReadonly();
  readonly saving = computed(() => this.busyMember() !== null);
  /** What went wrong in the last role change, if it failed. */
  readonly roleChangeProblem = this.lastRoleChangeProblem.asReadonly();
  /** What went wrong in the last removal, if it failed. */
  readonly removalProblem = this.lastRemovalProblem.asReadonly();

  /** Loads the members of the team of this id, and loads them again whenever the id changes. */
  follow(teamId: Signal<string>): void {
    this.teamId.set(teamId);
  }

  /** Asks the API for the list again, for example after a member was invited. */
  reload(): void {
    this.listing.reload();
  }

  /** Gives the member another role; resolves to whether the API accepted it. */
  changeRole(userId: string, role: TeamRole): Promise<boolean> {
    return this.run(userId, this.lastRoleChangeProblem, (teamId) =>
      this.port.changeRole(teamId, userId, role),
    );
  }

  /** Takes the member out of the team; resolves to whether the API accepted it. */
  remove(userId: string): Promise<boolean> {
    return this.run(userId, this.lastRemovalProblem, (teamId) => this.port.remove(teamId, userId));
  }

  /** Forgets the problem of the last removal, when its confirmation is opened or dismissed. */
  clearRemovalProblem(): void {
    this.lastRemovalProblem.set(null);
  }

  private async run(
    userId: string,
    problem: WritableSignal<MemberFailureKind | null>,
    command: (teamId: string) => Observable<void>,
  ): Promise<boolean> {
    const teamId = this.teamId()?.();
    if (teamId === undefined || this.busyMember() !== null) {
      return false;
    }
    this.busyMember.set(userId);
    this.lastRoleChangeProblem.set(null);
    this.lastRemovalProblem.set(null);
    try {
      await firstValueFrom(command(teamId), { defaultValue: undefined });
      return true;
    } catch (error: unknown) {
      problem.set(memberFailureKindOf(error));
      return false;
    } finally {
      this.busyMember.set(null);
      this.listing.reload();
    }
  }
}
