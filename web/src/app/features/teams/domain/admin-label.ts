import { type RoleLabel, type RoleOption } from './team-member';

/**
 * The label the roles list gives the admin role: how this team calls whoever manages it.
 * The messages that name that person use it. Before the list arrives there is nothing to
 * name, and `admin` is the plain word.
 */
export function adminLabelOf(roles: readonly RoleOption[]): RoleLabel {
  return roles.find((option) => option.role === 'admin')?.label ?? 'admin';
}
