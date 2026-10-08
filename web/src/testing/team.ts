import { type Team } from '@features/teams/domain/team';
import { type TeamRole } from '@features/teams/domain/team-member';

/** A team as the screens receive it. In support mode the admin is the Scrum Master. */
export function aTeam(id: string, name: string, role: TeamRole = 'admin'): Team {
  return {
    id,
    name,
    role,
    mode: 'support',
    label: role === 'admin' ? 'scrum_master' : 'member',
  };
}
