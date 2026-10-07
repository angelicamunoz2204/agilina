import { computed, inject, Injectable, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { TeamMembersPort } from './team-members.port';
import { memberFailureKindOf, type MemberFailureKind } from '../domain/member-failure';
import { type InvitationOutcome, type MemberInvitation } from '../domain/team-member';

/**
 * State of an invitation to a team: whether it is being sent, whether the last attempt failed
 * and what the last one that worked did. Provided by the invitation dialog, so it lives and
 * dies with it.
 *
 * A failed request becomes the problem the dialog translates; the HTTP interceptor has already
 * logged it, so it is not logged again here.
 */
@Injectable()
export class InviteMemberFacade {
  private readonly port = inject(TeamMembersPort);
  private readonly isSaving = signal(false);
  private readonly lastProblem = signal<MemberFailureKind | null>(null);
  private readonly lastOutcome = signal<InvitationOutcome | null>(null);

  readonly saving = this.isSaving.asReadonly();
  /** What went wrong in the last attempt, if it failed. */
  readonly problem = this.lastProblem.asReadonly();
  readonly failed = computed(() => this.lastProblem() !== null);
  /** What the last invitation that worked did. */
  readonly outcome = this.lastOutcome.asReadonly();

  /** Sends the invitation and resolves to what it did, or to null if the API refused it. */
  async invite(teamId: string, invitation: MemberInvitation): Promise<InvitationOutcome | null> {
    this.isSaving.set(true);
    this.lastProblem.set(null);
    try {
      const outcome = await firstValueFrom(this.port.invite(teamId, invitation));
      this.lastOutcome.set(outcome);
      return outcome;
    } catch (error: unknown) {
      this.lastProblem.set(memberFailureKindOf(error));
      return null;
    } finally {
      this.isSaving.set(false);
    }
  }
}
