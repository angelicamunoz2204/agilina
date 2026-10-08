import { type Observable } from 'rxjs';

import {
  type InvitationOutcome,
  type MemberInvitation,
  type TeamMembers,
  type TeamRole,
} from '../domain/team-member';

/**
 * Port towards the members of a team in the API. An abstract class so that it doubles as the
 * injection token; the HTTP adapter is bound in app.config.ts. Only an admin of the team gets
 * an answer: the API refuses everybody else.
 */
export abstract class TeamMembersPort {
  /** The active members of the team and the roles an admin can give them. */
  abstract list(teamId: string): Observable<TeamMembers>;

  /** Invites a person to the team and emits what the invitation did. */
  abstract invite(teamId: string, invitation: MemberInvitation): Observable<InvitationOutcome>;

  /** Gives a member another role in the team. */
  abstract changeRole(teamId: string, userId: string, role: TeamRole): Observable<void>;

  /** Takes a member out of the team; their account stays, it may belong to other teams. */
  abstract remove(teamId: string, userId: string): Observable<void>;
}
