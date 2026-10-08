import { type Observable } from 'rxjs';

import { type ActiveSprint } from '../domain/active-sprint';
import { type SprintDraft } from '../domain/sprint-draft';

/**
 * Port towards the sprint of a team in the API. An abstract class so that it doubles as the
 * injection token; the HTTP adapter is bound in app.config.ts. Any member of the team reads the
 * active sprint; only its admins create and edit it: the API refuses everybody else.
 */
export abstract class SprintsPort {
  /** The active sprint of the team with its day N of M, or null when the team has none. */
  abstract active(teamId: string): Observable<ActiveSprint | null>;

  /** Configures the sprint of a team that has no active one; it stays active. */
  abstract start(teamId: string, draft: SprintDraft): Observable<ActiveSprint>;

  /** Replaces the whole configuration of the team's active sprint. */
  abstract reconfigure(teamId: string, draft: SprintDraft): Observable<ActiveSprint>;
}
