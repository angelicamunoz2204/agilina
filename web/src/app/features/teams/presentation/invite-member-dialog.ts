import { Component, computed, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TranslocoDirective, TranslocoPipe } from '@jsverse/transloco';

import { Button } from '@shared/ui/button';
import { Dialog } from '@shared/ui/dialog';
import { Select } from '@shared/ui/select';
import { TextField } from '@shared/ui/text-field';

import { problemMessageKey } from './problem-message';
import { InviteMemberFacade } from '../application/invite-member.facade';
import { adminLabelOf } from '../domain/admin-label';
import {
  EMAIL_MAX_LENGTH,
  FULL_NAME_MAX_LENGTH,
  invitationProblems,
  isInvitationValid,
} from '../domain/member-invitation';
import { type InvitationOutcome, type RoleOption, type TeamRole } from '../domain/team-member';

/**
 * Dialog to invite a person to the team: their name, their email and the role they get,
 * Member unless the admin picks another. The API decides whether the email gets an
 * activation link or joins right away; the dialog tells the page which one happened. While the
 * invitation is on its way the dialog stays open, so that the page always learns the outcome.
 */
@Component({
  selector: 'agl-invite-member-dialog',
  imports: [FormsModule, TranslocoDirective, TranslocoPipe, Button, Dialog, Select, TextField],
  providers: [InviteMemberFacade],
  templateUrl: './invite-member-dialog.html',
})
export class InviteMemberDialog {
  readonly teamId = input.required<string>();
  /** The roles an admin can give, as the API lists them. */
  readonly roles = input.required<readonly RoleOption[]>();
  readonly invited = output<InvitationOutcome>();
  readonly dismissed = output();

  private readonly facade = inject(InviteMemberFacade);

  protected readonly nameMaxLength = FULL_NAME_MAX_LENGTH;
  protected readonly emailMaxLength = EMAIL_MAX_LENGTH;
  protected readonly fullName = signal('');
  protected readonly email = signal('');
  protected readonly role = signal<TeamRole>('member');
  /** Whether the user already typed in each field or left it: errors wait until then. */
  protected readonly nameTouched = signal(false);
  protected readonly emailTouched = signal(false);
  protected readonly problems = computed(() => invitationProblems(this.fullName(), this.email()));
  protected readonly canSend = computed(() => isInvitationValid(this.problems()));
  protected readonly nameProblem = computed(() =>
    this.nameTouched() ? this.problems().fullName : null,
  );
  protected readonly emailProblem = computed(() =>
    this.emailTouched() ? this.problems().email : null,
  );
  protected readonly adminLabel = computed(() => adminLabelOf(this.roles()));
  protected readonly saving = this.facade.saving;
  protected readonly problemMessage = computed(() => problemMessageKey(this.facade.problem()));

  protected changeName(name: string): void {
    this.fullName.set(name);
    this.nameTouched.set(true);
  }

  protected changeEmail(email: string): void {
    this.email.set(email);
    this.emailTouched.set(true);
  }

  /** Only a role the API offered can be picked. */
  protected changeRole(value: string): void {
    const option = this.roles().find((candidate) => candidate.role === value);
    if (option !== undefined) {
      this.role.set(option.role);
    }
  }

  protected async submit(): Promise<void> {
    if (!this.canSend() || this.saving()) {
      return;
    }
    const outcome = await this.facade.invite(this.teamId(), {
      fullName: this.fullName(),
      email: this.email(),
      role: this.role(),
    });
    if (outcome !== null) {
      this.invited.emit(outcome);
    }
  }
}
