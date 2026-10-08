import { Component, inject, input } from '@angular/core';
import { RouterLink } from '@angular/router';
import { TranslocoDirective } from '@jsverse/transloco';

import { TenantContext } from '@core/tenant/tenant-context';
import { Button } from '@shared/ui/button';

/**
 * "No access" for a section of the team settings, shown when the API refuses it (403): the
 * user is not an admin of the team, or not a member at all. Each section explains in `text`,
 * already translated, what only an admin can do there.
 */
@Component({
  selector: 'agl-settings-no-access',
  imports: [RouterLink, TranslocoDirective, Button],
  templateUrl: './settings-no-access.html',
})
export class SettingsNoAccess {
  readonly teamId = input.required<string>();
  readonly text = input.required<string>();

  protected readonly tenant = inject(TenantContext);
}
