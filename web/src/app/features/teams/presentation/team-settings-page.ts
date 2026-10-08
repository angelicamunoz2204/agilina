import { Component, computed, inject, input, type OnInit, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslocoDirective, TranslocoPipe } from '@jsverse/transloco';

import { TenantContext } from '@core/tenant/tenant-context';
import { Button } from '@shared/ui/button';
import { Select } from '@shared/ui/select';

import { InviteMemberDialog } from './invite-member-dialog';
import { problemMessageKey } from './problem-message';
import { RemoveMemberDialog } from './remove-member-dialog';
import { SettingsNoAccess } from './settings-no-access';
import { SettingsTabs } from './settings-tabs';
import { UserDetailDialog } from './user-detail-dialog';
import { TeamMembersFacade } from '../application/team-members.facade';
import { TeamShellFacade } from '../application/team-shell.facade';
import { adminLabelOf } from '../domain/admin-label';
import { type InvitationOutcome, type TeamMember } from '../domain/team-member';

/**
 * Settings → Team: the members of the team with their name, email and role, and what an admin
 * does with them (invite, change a role, remove). The screen does not decide who may open it
 * nor what may change: it shows what the API answers, disables what the API marks as blocked
 * with the API's reason, and shows "no access" when the API refuses the team. When that refusal
 * follows a change made here (an admin demoted or removed themself), it says so instead.
 */
@Component({
  selector: 'agl-team-settings-page',
  imports: [
    RouterLink,
    TranslocoDirective,
    TranslocoPipe,
    Button,
    Select,
    InviteMemberDialog,
    RemoveMemberDialog,
    SettingsNoAccess,
    SettingsTabs,
    UserDetailDialog,
  ],
  providers: [TeamMembersFacade, TeamShellFacade],
  templateUrl: './team-settings-page.html',
})
export class TeamSettingsPage implements OnInit {
  /** The :teamId of the route, bound by the router (withComponentInputBinding). */
  readonly teamId = input.required<string>();

  private readonly facade = inject(TeamMembersFacade);
  private readonly shell = inject(TeamShellFacade);
  protected readonly tenant = inject(TenantContext);

  protected readonly members = this.facade.members;
  protected readonly roles = this.facade.roles;
  /** How this team calls whoever manages it, for the messages that name that person. */
  protected readonly adminLabel = computed(() => adminLabelOf(this.roles()));
  protected readonly loading = this.facade.loading;
  protected readonly saving = this.facade.saving;
  protected readonly savingMember = this.facade.savingMember;
  /** The API refused the team to this user: not an admin of it, or not a member at all. */
  protected readonly forbidden = computed(() => this.facade.problem() === 'forbidden');
  /** The last change saved here, if any: a refusal after it means it took the access away. */
  private readonly lastChange = signal<'role_change' | 'removal' | null>(null);
  protected readonly lostAccess = computed(() => (this.forbidden() ? this.lastChange() : null));
  protected readonly problemMessage = computed(() =>
    this.forbidden() ? null : problemMessageKey(this.facade.problem()),
  );
  protected readonly roleChangeMessage = computed(() =>
    problemMessageKey(this.facade.roleChangeProblem()),
  );
  protected readonly removalMessage = computed(() =>
    problemMessageKey(this.facade.removalProblem()),
  );

  protected readonly inviting = signal(false);
  protected readonly removing = signal<TeamMember | null>(null);
  protected readonly viewing = signal<TeamMember | null>(null);
  protected readonly lastInvitation = signal<InvitationOutcome | null>(null);

  ngOnInit(): void {
    this.facade.follow(this.teamId);
    this.shell.follow(this.teamId);
  }

  protected openInvitation(): void {
    this.lastInvitation.set(null);
    this.inviting.set(true);
  }

  protected invited(outcome: InvitationOutcome): void {
    this.inviting.set(false);
    this.lastInvitation.set(outcome);
    this.facade.reload();
  }

  protected async changeRole(member: TeamMember, control: HTMLSelectElement): Promise<void> {
    const role = this.roles().find((option) => option.role === control.value)?.role;
    if (role === undefined || role === member.role) {
      return;
    }
    const changed = await this.facade.changeRole(member.userId, role);
    if (changed) {
      this.lastChange.set('role_change');
      // It may have been my own role: the top bar shows the one the API has now.
      this.shell.refresh();
    } else {
      // The API kept the old role: the control shows it again.
      control.value = member.role;
    }
  }

  protected askToRemove(member: TeamMember): void {
    this.facade.clearRemovalProblem();
    this.removing.set(member);
  }

  protected cancelRemoval(): void {
    this.removing.set(null);
    this.facade.clearRemovalProblem();
  }

  protected async confirmRemoval(): Promise<void> {
    const member = this.removing();
    if (member === null) {
      return;
    }
    if (await this.facade.remove(member.userId)) {
      this.lastChange.set('removal');
      this.removing.set(null);
      this.shell.refresh();
    }
  }
}
