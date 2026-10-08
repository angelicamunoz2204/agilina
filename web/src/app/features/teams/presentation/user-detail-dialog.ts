import { Component, computed, inject, input, type OnInit, output } from '@angular/core';
import { TranslocoDirective, TranslocoPipe, TranslocoService } from '@jsverse/transloco';

import { Button } from '@shared/ui/button';
import { Dialog } from '@shared/ui/dialog';
import { formatDate } from '@shared/utils/format-date';

import { problemMessageKey } from './problem-message';
import { UserDetailFacade } from '../application/user-detail.facade';
import { adminLabelOf } from '../domain/admin-label';
import { type RoleOption, type TeamMember } from '../domain/team-member';

/**
 * The detail of one user of the team, in a dialog: who they are, how the team calls them, since
 * when they are in it and why their role cannot change or they cannot be removed. It shows the
 * row it was opened from at once and asks the API for the user, so it never shows more than
 * the API says. It only informs; the settings page owns the changes.
 */
@Component({
  selector: 'agl-user-detail-dialog',
  imports: [TranslocoDirective, TranslocoPipe, Button, Dialog],
  providers: [UserDetailFacade],
  templateUrl: './user-detail-dialog.html',
})
export class UserDetailDialog implements OnInit {
  readonly teamId = input.required<string>();
  /** The row the dialog was opened from. */
  readonly member = input.required<TeamMember>();
  /** The roles an admin can give, to name whoever manages the team in the messages. */
  readonly roles = input.required<readonly RoleOption[]>();
  readonly dismissed = output();

  private readonly facade = inject(UserDetailFacade);
  private readonly transloco = inject(TranslocoService);

  /** The user as the API gave them, or the row while the API has not answered. */
  protected readonly shown = computed(() => this.facade.user() ?? this.member());
  protected readonly loading = this.facade.loading;
  protected readonly problemMessage = computed(() => problemMessageKey(this.facade.problem()));
  protected readonly adminLabel = computed(() => adminLabelOf(this.roles()));
  protected readonly joined = computed(() =>
    formatDate(this.shown().joinedAt, this.transloco.getActiveLang()),
  );

  ngOnInit(): void {
    this.facade.follow(this.teamId(), this.member().userId);
  }
}
