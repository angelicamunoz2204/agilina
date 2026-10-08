import { type RoleLabel, type TeamRole } from './team-member';

/** How Agilina works in a team: whether a human Scrum Master approves its actions. */
export type TeamMode = 'support' | 'autonomous';

/**
 * A team the user belongs to, as the screens show it: its id, its name and the user's internal
 * role in it. The role only decides what the screens offer (the link to the team settings);
 * the API is the one that authorizes.
 */
export interface Team {
  id: string;
  name: string;
  role: TeamRole;
  /** How the role is shown to the user in this team (HU-04). */
  label: RoleLabel;
  mode: TeamMode;
}
