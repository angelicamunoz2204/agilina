import { type AbstractControl, type ValidationErrors } from '@angular/forms';

import { teamNameProblem, type TeamNameProblem } from '../domain/team-name';

/** Key under which teamNameValidator reports its problem in the control's errors. */
const TEAM_NAME_ERROR = 'teamName';

/**
 * Form validator of a team name. It only delegates to the pure rule of the domain:
 * the form gives quick feedback, the API has the last word.
 */
export function teamNameValidator(control: AbstractControl<string>): ValidationErrors | null {
  const problem = teamNameProblem(control.value);
  return problem === null ? null : { [TEAM_NAME_ERROR]: problem };
}

/** The problem teamNameValidator found in this control, if any. */
export function teamNameError(control: AbstractControl<string>): TeamNameProblem | null {
  return (control.getError(TEAM_NAME_ERROR) as TeamNameProblem | undefined) ?? null;
}
