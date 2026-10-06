import { type MemberFailureKind } from '../domain/member-failure';
import { type TeamFailureKind } from '../domain/team-failure';

/**
 * The key of the message a screen shows for a problem, inside that screen's texts: each
 * screen words it for its own context, and an unexpected failure uses its `failed` text.
 */
export function problemMessageKey(
  problem: TeamFailureKind | MemberFailureKind | null,
): string | null {
  if (problem === null) {
    return null;
  }
  return problem === 'unavailable' ? 'failed' : `problems.${problem}`;
}
