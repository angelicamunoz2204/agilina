import { type RoleLabel } from '../domain/team-member';

/** A label this app does not know is shown as the least: it reads as `member`. */
export function toRoleLabel(label: string): RoleLabel {
  return label === 'scrum_master' || label === 'admin' ? label : 'member';
}
