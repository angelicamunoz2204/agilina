import { Component, inject } from '@angular/core';
import { FormControl, FormGroup, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { TranslocoDirective } from '@jsverse/transloco';

import { teamNameError, teamNameValidator } from './team-name.validator';
import { CreateTeamFacade } from '../application/create-team.facade';
import { TEAM_NAME_MAX_LENGTH, type TeamNameProblem } from '../domain/team-name';

/**
 * Form to create a team: only its name. Mode and language take the defaults of every
 * new team, and whoever creates it becomes its admin; the API decides both.
 */
@Component({
  selector: 'agl-create-team-page',
  imports: [ReactiveFormsModule, RouterLink, TranslocoDirective],
  providers: [CreateTeamFacade],
  templateUrl: './create-team-page.html',
  styleUrl: './create-team-page.scss',
})
export class CreateTeamPage {
  private readonly facade = inject(CreateTeamFacade);
  private readonly router = inject(Router);

  protected readonly maxLength = TEAM_NAME_MAX_LENGTH;
  protected readonly form = new FormGroup({
    name: new FormControl('', { nonNullable: true, validators: [teamNameValidator] }),
  });
  protected readonly saving = this.facade.saving;
  protected readonly failed = this.facade.failed;

  /** The problem to show, once the user has typed in the field or left it. */
  protected nameProblem(): TeamNameProblem | null {
    const name = this.form.controls.name;
    return name.dirty || name.touched ? teamNameError(name) : null;
  }

  protected async submit(): Promise<void> {
    if (this.form.invalid || this.saving()) {
      return;
    }
    const teamId = await this.facade.create(this.form.controls.name.value);
    if (teamId !== null) {
      await this.router.navigate(['/teams', teamId]);
    }
  }
}
