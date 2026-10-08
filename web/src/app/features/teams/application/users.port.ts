import { type Observable } from 'rxjs';

import {
  type InvitationOutcome,
  type MemberInvitation,
  type MyMembership,
  type TeamMember,
  type TeamMembers,
  type TeamRole,
} from '../domain/team-member';

/**
 * Port towards the users API: the people of a team and the caller as one of them. An abstract class so that it doubles as the
 * injection token; the HTTP adapter is bound in app.config.ts. Only an admin of the team gets
 * an answer: the API refuses everybody else.
 */
export abstract class UsersPort {
  /** The active members of the team and the roles an admin can give them. */
  abstract list(teamId: string): Observable<TeamMembers>;

  /** One active member of the team, for the detail dialog. */
  abstract get(teamId: string, userId: string): Observable<TeamMember>;

  /** The caller as a member of the team, for the app header. Any member of the team may ask. */
  abstract me(teamId: string): Observable<MyMembership>;

  /** Invites a person to the team and emits what the invitation did. */
  abstract invite(teamId: string, invitation: MemberInvitation): Observable<InvitationOutcome>;

  /** Gives a member another role in the team. */
  abstract changeRole(teamId: string, userId: string, role: TeamRole): Observable<void>;

  /** Takes a member out of the team; their account stays, it may belong to other teams. */
  abstract remove(teamId: string, userId: string): Observable<void>;
}
