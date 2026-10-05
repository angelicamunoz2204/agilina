export type TeamRole = 'admin' | 'member';

/** What the activation page knows about an invitation that can still be used. */
export interface Invitation {
  readonly email: string;
  readonly fullName: string;
  readonly role: TeamRole;
  readonly expiresAt: Date;
}

/** The account created from an invitation: who, in which team and with which role. */
export interface ActivatedAccount {
  readonly email: string;
  readonly teamId: string;
  readonly role: TeamRole;
}
