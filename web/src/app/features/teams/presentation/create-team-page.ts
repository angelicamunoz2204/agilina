import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { TranslocoDirective } from '@jsverse/transloco';

import { TenantContext } from '@core/tenant/tenant-context';
import { Button } from '@shared/ui/button';
import { TextField } from '@shared/ui/text-field';

import { problemMessageKey } from './problem-message';
import { CreateTeamFacade } from '../application/create-team.facade';
import { TEAM_NAME_MAX_LENGTH, teamNameProblem } from '../domain/team-name';

/**
 * Form to create a team: only its name. Mode and language take the defaults of every
 * new team, and whoever creates it becomes its admin; the API decides both.
 */
@Component({
  selector: 'agl-create-team-page',
  imports: [FormsModule, RouterLink, TranslocoDirective, Button, TextField],
  providers: [CreateTeamFacade],
  templateUrl: './create-team-page.html',
})
export class CreateTeamPage {
  private readonly facade = inject(CreateTeamFacade);
  private readonly router = inject(Router);
  protected readonly tenant = inject(TenantContext);

  protected readonly maxLength = TEAM_NAME_MAX_LENGTH;
  protected readonly name = signal('');
  /** Whether the user already typed in the field or left it: errors wait until then. */
  protected readonly touched = signal(false);
  protected readonly problem = computed(() => teamNameProblem(this.name()));
  protected readonly shownProblem = computed(() => (this.touched() ? this.problem() : null));
  protected readonly saving = this.facade.saving;
  protected readonly problemMessage = computed(() => problemMessageKey(this.facade.problem()));

  protected changeName(name: string): void {
    this.name.set(name);
    this.touched.set(true);
  }

  protected async submit(): Promise<void> {
    if (this.problem() !== null || this.saving()) {
      return;
    }
    const teamId = await this.facade.create(this.name());
    if (teamId !== null) {
      await this.router.navigate(this.tenant.path('teams', teamId));
    }
  }
}
