import { computed, inject, Injectable, signal, type Signal } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';
import { firstValueFrom } from 'rxjs';

import { BROWSER_TIME_ZONE } from '@core/time/browser-time-zone';
import { localDateTimeToIso } from '@shared/utils/local-date-time';

import { SprintsPort } from './sprints.port';
import { TeamMembersPort } from './team-members.port';
import { type ActiveSprint } from '../domain/active-sprint';
import { memberFailureKindOf, type MemberFailureKind } from '../domain/member-failure';
import { type SprintDraft, type SprintFields } from '../domain/sprint-draft';
import { sprintFailureKindOf, type SprintFailureKind } from '../domain/sprint-failure';
import { type TeamMember } from '../domain/team-member';

/**
 * State of Settings → Sprint: the active sprint of the team whose id the page receives, the
 * members to pick the daily's participants from, and saving it. Provided by the page, so it
 * lives and dies with it.
 *
 * Saving creates the sprint when the team has none and edits it otherwise; the answer of the
 * API replaces the sprint shown, so the day N of M and the next daily are the API's. The daily's
 * time always travels with the browser's time zone (AD-31). A failed request becomes a problem
 * the screen translates; the HTTP interceptor has already logged it, so it is not logged again.
 */
@Injectable()
export class SprintSettingsFacade {
  private readonly sprints = inject(SprintsPort);
  private readonly membersPort = inject(TeamMembersPort);
  private readonly browserTimeZone = inject(BROWSER_TIME_ZONE);
  private readonly teamId = signal<Signal<string> | null>(null);
  private readonly activeSprint = rxResource({
    params: () => this.teamId()?.(),
    stream: ({ params }) => this.sprints.active(params),
  });
  private readonly listing = rxResource({
    params: () => this.teamId()?.(),
    stream: ({ params }) => this.membersPort.list(params),
  });
  private readonly isSaving = signal(false);
  private readonly lastProblem = signal<SprintFailureKind | null>(null);
  private readonly hasSaved = signal(false);

  /** The time zone the daily's time is saved with: the browser's. */
  readonly timeZone = this.browserTimeZone;
  /** The active sprint, or null when the team has none; undefined until the API answers. */
  readonly sprint = computed<ActiveSprint | null | undefined>(() =>
    this.activeSprint.hasValue() ? this.activeSprint.value() : undefined,
  );
  /** The members to pick the participants from; null until the API answers. */
  readonly members = computed<readonly TeamMember[] | null>(() =>
    this.listing.hasValue() ? this.listing.value().members : null,
  );
  /** Whether both the sprint and the members are known, so that the form can be filled. */
  readonly ready = computed(() => this.sprint() !== undefined && this.members() !== null);
  readonly loading = computed(() => this.activeSprint.isLoading() || this.listing.isLoading());
  /** What went wrong loading the screen, if anything did. */
  readonly problem = computed<SprintFailureKind | MemberFailureKind | null>(() => {
    if (this.listing.status() === 'error') {
      return memberFailureKindOf(this.listing.error());
    }
    if (this.activeSprint.status() === 'error') {
      return sprintFailureKindOf(this.activeSprint.error());
    }
    return null;
  });
  readonly saving = this.isSaving.asReadonly();
  /** What went wrong in the last save, if it failed. */
  readonly saveProblem = this.lastProblem.asReadonly();
  /** Whether the last save worked. */
  readonly saved = this.hasSaved.asReadonly();

  /** Loads the sprint and members of the team of this id, and again whenever the id changes. */
  follow(teamId: Signal<string>): void {
    this.teamId.set(teamId);
  }

  /** Saves the sprint as the form holds it; resolves to whether the API accepted it. */
  async save(fields: SprintFields): Promise<boolean> {
    const teamId = this.teamId()?.();
    const sprint = this.sprint();
    if (teamId === undefined || sprint === undefined || this.isSaving()) {
      return false;
    }
    const draft: SprintDraft = {
      startDate: fields.startDate,
      endDate: fields.endDate,
      dailyTime: localDateTimeToIso(fields.startDate, fields.dailyTime),
      timeZone: this.browserTimeZone,
      participants: fields.participants,
    };
    this.isSaving.set(true);
    this.lastProblem.set(null);
    this.hasSaved.set(false);
    try {
      const saved = await firstValueFrom(
        sprint === null
          ? this.sprints.start(teamId, draft)
          : this.sprints.reconfigure(teamId, draft),
      );
      this.activeSprint.set(saved);
      this.hasSaved.set(true);
      return true;
    } catch (error: unknown) {
      const problem = sprintFailureKindOf(error);
      this.lastProblem.set(problem);
      if (problem === 'active_sprint_exists' || problem === 'no_active_sprint') {
        // Someone else created or closed the sprint meanwhile: the next save must know it.
        this.activeSprint.reload();
      }
      return false;
    } finally {
      this.isSaving.set(false);
    }
  }
}
