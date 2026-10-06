/** Longest team name accepted, counted once the surrounding spaces are trimmed. */
export const TEAM_NAME_MAX_LENGTH = 80;

/** Why a team name cannot be saved. */
export type TeamNameProblem = 'blank' | 'too_long';

/**
 * The team name rule: trimmed, not blank and at most TEAM_NAME_MAX_LENGTH characters.
 *
 * Characters are counted as code points (`Array.from(name).length`), the way the API
 * and the database count them, so an emoji is one character and not two UTF-16 units
 * (`name.length` would count those). This is a convenience for the user: the API
 * applies the same rule and has the last word.
 */
export function teamNameProblem(raw: string): TeamNameProblem | null {
  const name = raw.trim();
  if (name === '') {
    return 'blank';
  }
  return Array.from(name).length > TEAM_NAME_MAX_LENGTH ? 'too_long' : null;
}
