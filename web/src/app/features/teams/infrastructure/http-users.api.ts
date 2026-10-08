import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, type Observable, throwError } from 'rxjs';

import { RUNTIME_CONFIG } from '@core/config/runtime-config';
import { readApiError } from '@core/http/api-error';

import { toRoleLabel } from './role-label';
import { toTeamRole } from './team-role';
import { type UsersPort } from '../application/users.port';
import { MemberFailure, type MemberFailureKind } from '../domain/member-failure';
import {
  type InvitationOutcome,
  type MemberChangeBlocker,
  type MemberInvitation,
  type MyMembership,
  type RoleOption,
  type TeamMember,
  type TeamMembers,
  type TeamRole,
} from '../domain/team-member';

/** Body of GET /v1/users?team_id=…, exactly as the API sends it. */
interface UsersInTeamResponse {
  roles: RoleOptionResponse[];
  users: UserInTeamResponse[];
}

interface RoleOptionResponse {
  role: string;
  label: string;
}

/** One user of a team: GET /v1/users/{user_id}?team_id=… and each item of the list. */
interface UserInTeamResponse {
  user_id: string;
  full_name: string;
  email: string;
  role: string;
  label: string;
  joined_at: string;
  role_change_blocked_by: MemberChangeBlocker | null;
  removal_blocked_by: MemberChangeBlocker | null;
}

/** Body of GET /v1/users/me?team_id=…. */
interface MeResponse {
  user_id: string;
  full_name: string;
  email: string;
  role: string;
  label: string;
  joined_at: string;
}

/** Body of PATCH /v1/users/{user_id}?team_id=…. */
interface ChangeMemberRoleRequest {
  role: TeamRole;
}

/** Body of POST /v1/users/invitations?team_id=…. */
interface InviteToTeamRequest {
  full_name: string;
  email: string;
  role: TeamRole;
}

/** Body of the 201 answer of POST /v1/users/invitations. */
interface InviteToTeamResponse {
  outcome: InvitationOutcome;
}

const FAILURES: Readonly<Record<string, MemberFailureKind>> = {
  not_authenticated: 'not_authenticated',
  // Someone else's team and a team where the user is not an admin read the same: no access.
  not_a_team_member: 'forbidden',
  not_a_team_admin: 'forbidden',
  member_not_found: 'not_found',
  already_a_team_member: 'already_member',
  account_disabled: 'account_disabled',
  invalid_email: 'invalid_email',
  invalid_full_name: 'invalid_name',
  last_admin: 'last_admin',
  sprint_in_progress: 'sprint_in_progress',
  mail_unavailable: 'mail_unavailable',
};

/** HTTP adapter of the users port: list, read, me, invite, change a role and remove. */
@Injectable()
export class HttpUsersApi implements UsersPort {
  private readonly http = inject(HttpClient);
  private readonly usersUrl = `${inject(RUNTIME_CONFIG).apiUrl}/v1/users`;

  list(teamId: string): Observable<TeamMembers> {
    return this.http
      .get<UsersInTeamResponse>(this.usersUrl, { params: { team_id: teamId } })
      .pipe(map(toTeamMembers), catchError(failWithDomainError));
  }

  get(teamId: string, userId: string): Observable<TeamMember> {
    return this.http
      .get<UserInTeamResponse>(this.userUrl(userId), { params: { team_id: teamId } })
      .pipe(map(toTeamMember), catchError(failWithDomainError));
  }

  me(teamId: string): Observable<MyMembership> {
    return this.http
      .get<MeResponse>(`${this.usersUrl}/me`, { params: { team_id: teamId } })
      .pipe(map(toMyMembership), catchError(failWithDomainError));
  }

  invite(teamId: string, invitation: MemberInvitation): Observable<InvitationOutcome> {
    const body: InviteToTeamRequest = {
      full_name: invitation.fullName,
      email: invitation.email,
      role: invitation.role,
    };
    return this.http
      .post<InviteToTeamResponse>(`${this.usersUrl}/invitations`, body, {
        params: { team_id: teamId },
      })
      .pipe(
        map((response) => response.outcome),
        catchError(failWithDomainError),
      );
  }

  changeRole(teamId: string, userId: string, role: TeamRole): Observable<void> {
    const body: ChangeMemberRoleRequest = { role };
    return this.http.patch(this.userUrl(userId), body, { params: { team_id: teamId } }).pipe(
      map(() => undefined),
      catchError(failWithDomainError),
    );
  }

  remove(teamId: string, userId: string): Observable<void> {
    return this.http.delete(this.userUrl(userId), { params: { team_id: teamId } }).pipe(
      map(() => undefined),
      catchError(failWithDomainError),
    );
  }

  private userUrl(userId: string): string {
    return `${this.usersUrl}/${encodeURIComponent(userId)}`;
  }
}

/** The API contract stays in this file; the rest of the app sees the domain model. */
function toTeamMembers(response: UsersInTeamResponse): TeamMembers {
  return { roles: response.roles.map(toRoleOption), members: response.users.map(toTeamMember) };
}

function toRoleOption(response: RoleOptionResponse): RoleOption {
  return { role: toTeamRole(response.role), label: toRoleLabel(response.label) };
}

function toTeamMember(response: UserInTeamResponse): TeamMember {
  return {
    userId: response.user_id,
    fullName: response.full_name,
    email: response.email,
    role: toTeamRole(response.role),
    label: toRoleLabel(response.label),
    joinedAt: new Date(response.joined_at),
    roleChangeBlockedBy: response.role_change_blocked_by,
    removalBlockedBy: response.removal_blocked_by,
  };
}

function toMyMembership(response: MeResponse): MyMembership {
  return {
    userId: response.user_id,
    fullName: response.full_name,
    email: response.email,
    role: toTeamRole(response.role),
    label: toRoleLabel(response.label),
    joinedAt: new Date(response.joined_at),
  };
}

/** The API's error codes stay in this file: the rest of the app only sees `MemberFailure`. */
function failWithDomainError(error: unknown): Observable<never> {
  return throwError(() => toFailure(error));
}

function toFailure(error: unknown): MemberFailure {
  if (!(error instanceof HttpErrorResponse)) {
    return new MemberFailure('unavailable');
  }
  const body = readApiError(error.error);
  return new MemberFailure((body !== undefined ? FAILURES[body.code] : undefined) ?? 'unavailable');
}
