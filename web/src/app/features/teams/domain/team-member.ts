/** A person's internal role in a team: the only thing authorization looks at. */
export type TeamRole = 'admin' | 'member';

/**
 * Code of the label a screen shows for a role; the screen translates it. The API sends it
 * and the client never derives it: today it is the role itself, and HU-04 derives it from the
 * role and the team's mode.
 */
export type RoleLabel = 'admin' | 'member';

/** Why the API does not let a member's role change, or the member be removed, right now. */
export type MemberChangeBlocker = 'last_admin' | 'sprint_in_progress';

/** A role an admin can give, with the label to show for it. */
export interface RoleOption {
  readonly role: TeamRole;
  readonly label: RoleLabel;
}

/** An active member of a team, as the team settings show it. */
export interface TeamMember {
  readonly userId: string;
  readonly fullName: string;
  readonly email: string;
  readonly role: TeamRole;
  readonly label: RoleLabel;
  /** Why the role cannot change now, or null when it can. */
  readonly roleChangeBlockedBy: MemberChangeBlocker | null;
  /** Why the member cannot be removed now, or null when they can. */
  readonly removalBlockedBy: MemberChangeBlocker | null;
}

/** The members of a team and the roles an admin can give them, in the order to show them. */
export interface TeamMembers {
  readonly roles: readonly RoleOption[];
  readonly members: readonly TeamMember[];
}

/** Who to invite to a team and with which role. */
export interface MemberInvitation {
  readonly fullName: string;
  readonly email: string;
  readonly role: TeamRole;
}

/**
 * What inviting did: an email without an account got an invitation with its activation link;
 * one with an account joined the team right away and got a notice.
 */
export type InvitationOutcome = 'invitation_sent' | 'member_added';
