import { type TeamRole } from './team-member';

/**
 * A team the user belongs to, as the screens show it: its id, its name and the user's internal
 * role in it. The role only decides what the screens offer (the link to the team settings);
 * the API is the one that authorizes.
 */
export interface Team {
  id: string;
  name: string;
  role: TeamRole;
}
