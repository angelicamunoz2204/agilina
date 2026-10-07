import { Component, input, output } from '@angular/core';
import { TranslocoDirective } from '@jsverse/transloco';

import { Button } from '@shared/ui/button';
import { Dialog } from '@shared/ui/dialog';

import { type TeamMember } from '../domain/team-member';

/**
 * Confirmation before taking a member out of the team: it warns that the person stops
 * getting the team's calls. It only asks; the page removes and tells it how it went.
 */
@Component({
  selector: 'agl-remove-member-dialog',
  imports: [TranslocoDirective, Button, Dialog],
  templateUrl: './remove-member-dialog.html',
})
export class RemoveMemberDialog {
  readonly member = input.required<TeamMember>();
  readonly saving = input(false);
  /** Key of the message of the last failed attempt, inside `teams.settings.remove`. */
  readonly problem = input<string | null>(null);
  readonly confirmed = output();
  readonly dismissed = output();
}
