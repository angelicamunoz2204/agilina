import { type TeamRole } from '../domain/team-member';

/** A role this app does not know offers the least: it reads as `member`. */
export function toTeamRole(role: string): TeamRole {
  return role === 'admin' ? 'admin' : 'member';
}
