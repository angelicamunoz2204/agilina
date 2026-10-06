import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, type Observable, throwError } from 'rxjs';

import { RUNTIME_CONFIG } from '@core/config/runtime-config';

import { type TeamMembersPort } from '../application/team-members.port';
import { MemberFailure, type MemberFailureKind } from '../domain/member-failure';
import {
  type InvitationOutcome,
  type MemberChangeBlocker,
  type MemberInvitation,
  type RoleLabel,
  type RoleOption,
  type TeamMember,
  type TeamMembers,
  type TeamRole,
} from '../domain/team-member';

/** Body of GET /v1/teams/{team_id}/members, exactly as the API sends it. */
interface TeamMembersResponse {
  roles: RoleOptionResponse[];
  members: TeamMemberResponse[];
}

interface RoleOptionResponse {
  role: string;
  label: string;
}

interface TeamMemberResponse {
  user_id: string;
  full_name: string;
  email: string;
  role: string;
  label: string;
  role_change_blocked_by: MemberChangeBlocker | null;
  removal_blocked_by: MemberChangeBlocker | null;
}

/** Body of PATCH /v1/teams/{team_id}/members/{user_id}. */
interface ChangeMemberRoleRequest {
  role: TeamRole;
}

/** Body of POST /v1/teams/{team_id}/invitations. */
interface InviteToTeamRequest {
  full_name: string;
  email: string;
  role: TeamRole;
}

/** Body of the 201 answer of POST /v1/teams/{team_id}/invitations. */
interface InviteToTeamResponse {
  outcome: InvitationOutcome;
}

/** Every error of the API has a stable `code`. */
interface ErrorResponse {
  code?: string;
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

/** HTTP adapter of the team members port: list, invite, change a role and remove. */
@Injectable()
export class HttpTeamMembersApi implements TeamMembersPort {
  private readonly http = inject(HttpClient);
  private readonly teamsUrl = `${inject(RUNTIME_CONFIG).apiUrl}/v1/teams`;

  list(teamId: string): Observable<TeamMembers> {
    return this.http
      .get<TeamMembersResponse>(this.membersUrl(teamId))
      .pipe(map(toTeamMembers), catchError(failWithDomainError));
  }

  invite(teamId: string, invitation: MemberInvitation): Observable<InvitationOutcome> {
    const body: InviteToTeamRequest = {
      full_name: invitation.fullName,
      email: invitation.email,
      role: invitation.role,
    };
    return this.http.post<InviteToTeamResponse>(`${this.teamUrl(teamId)}/invitations`, body).pipe(
      map((response) => response.outcome),
      catchError(failWithDomainError),
    );
  }

  changeRole(teamId: string, userId: string, role: TeamRole): Observable<void> {
    const body: ChangeMemberRoleRequest = { role };
    return this.http.patch(this.memberUrl(teamId, userId), body).pipe(
      map(() => undefined),
      catchError(failWithDomainError),
    );
  }

  remove(teamId: string, userId: string): Observable<void> {
    return this.http.delete(this.memberUrl(teamId, userId)).pipe(
      map(() => undefined),
      catchError(failWithDomainError),
    );
  }

  private teamUrl(teamId: string): string {
    return `${this.teamsUrl}/${encodeURIComponent(teamId)}`;
  }

  private membersUrl(teamId: string): string {
    return `${this.teamUrl(teamId)}/members`;
  }

  private memberUrl(teamId: string, userId: string): string {
    return `${this.membersUrl(teamId)}/${encodeURIComponent(userId)}`;
  }
}

/** The API contract stays in this file; the rest of the app sees the domain model. */
function toTeamMembers(response: TeamMembersResponse): TeamMembers {
  return { roles: response.roles.map(toRoleOption), members: response.members.map(toTeamMember) };
}

function toRoleOption(response: RoleOptionResponse): RoleOption {
  return { role: toRole(response.role), label: toLabel(response.label) };
}

function toTeamMember(response: TeamMemberResponse): TeamMember {
  return {
    userId: response.user_id,
    fullName: response.full_name,
    email: response.email,
    role: toRole(response.role),
    label: toLabel(response.label),
    roleChangeBlockedBy: response.role_change_blocked_by,
    removalBlockedBy: response.removal_blocked_by,
  };
}

/** A role this screen does not know offers the least: it reads as `member`. */
function toRole(role: string): TeamRole {
  return role === 'admin' ? 'admin' : 'member';
}

/** Until HU-04 the label is the role's own code, so it reads the same way. */
function toLabel(label: string): RoleLabel {
  return label === 'admin' ? 'admin' : 'member';
}

/** The API's error codes stay in this file: the rest of the app only sees `MemberFailure`. */
function failWithDomainError(error: unknown): Observable<never> {
  return throwError(() => toFailure(error));
}

function toFailure(error: unknown): MemberFailure {
  if (!(error instanceof HttpErrorResponse)) {
    return new MemberFailure('unavailable');
  }
  const body = asErrorResponse(error.error);
  return new MemberFailure(
    (body.code !== undefined ? FAILURES[body.code] : undefined) ?? 'unavailable',
  );
}

function asErrorResponse(body: unknown): ErrorResponse {
  return typeof body === 'object' && body !== null ? body : {};
}
