import { Component, inject, input } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { TranslocoDirective } from '@jsverse/transloco';

import { TenantContext } from '@core/tenant/tenant-context';

/**
 * The heading of the team settings and its sections, Team and Sprint, as links: each section is
 * its own address, and the current one is marked with `aria-current="page"`.
 */
@Component({
  selector: 'agl-settings-tabs',
  imports: [RouterLink, RouterLinkActive, TranslocoDirective],
  templateUrl: './settings-tabs.html',
})
export class SettingsTabs {
  readonly teamId = input.required<string>();

  protected readonly tenant = inject(TenantContext);
}
