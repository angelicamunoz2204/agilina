import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { catchError, map, type Observable, throwError } from 'rxjs';

import { RUNTIME_CONFIG } from '@core/config/runtime-config';

import { type TeamsPort } from '../application/teams.port';
import { type Team } from '../domain/team';
import { TeamFailure, type TeamFailureKind } from '../domain/team-failure';

/** Item of GET /v1/teams, exactly as the API sends it. */
interface MyTeamResponse {
  id: string;
  name: string;
  role: string;
}

/** Body of POST /v1/teams. */
interface CreateTeamRequest {
  name: string;
}

/** Body of the 201 answer of POST /v1/teams. */
interface CreatedTeamResponse {
  id: string;
}

/** Body of GET /v1/teams/{team_id}. */
interface TeamResponse {
  id: string;
  name: string;
  mode: string;
  language: string;
  role: string;
}

/** Every error of the API has a stable `code`. */
interface ErrorResponse {
  code?: string;
}

const FAILURES: Readonly<Record<string, TeamFailureKind>> = {
  not_authenticated: 'not_authenticated',
  invalid_team_name: 'invalid_name',
  not_a_team_member: 'not_a_member',
};

/** HTTP adapter of the teams port: the only exit of this feature towards the API. */
@Injectable()
export class HttpTeamsApi implements TeamsPort {
  private readonly http = inject(HttpClient);
  private readonly teamsUrl = `${inject(RUNTIME_CONFIG).apiUrl}/v1/teams`;

  listMine(): Observable<readonly Team[]> {
    return this.http.get<MyTeamResponse[]>(this.teamsUrl).pipe(
      map((teams) => teams.map(toTeam)),
      catchError(failWithDomainError),
    );
  }

  create(name: string): Observable<string> {
    const body: CreateTeamRequest = { name };
    return this.http.post<CreatedTeamResponse>(this.teamsUrl, body).pipe(
      map((created) => created.id),
      catchError(failWithDomainError),
    );
  }

  get(teamId: string): Observable<Team> {
    return this.http
      .get<TeamResponse>(`${this.teamsUrl}/${encodeURIComponent(teamId)}`)
      .pipe(map(toTeam), catchError(failWithDomainError));
  }
}

/**
 * The API contract stays in this file; the rest of the app sees the domain model.
 * The role, mode and language are not shown yet, so they do not reach the domain.
 */
function toTeam(response: MyTeamResponse | TeamResponse): Team {
  return { id: response.id, name: response.name };
}

/** The API's error codes stay in this file: the rest of the app only sees `TeamFailure`. */
function failWithDomainError(error: unknown): Observable<never> {
  return throwError(() => toFailure(error));
}

function toFailure(error: unknown): TeamFailure {
  if (!(error instanceof HttpErrorResponse)) {
    return new TeamFailure('unavailable');
  }
  const body = asErrorResponse(error.error);
  return new TeamFailure(
    (body.code !== undefined ? FAILURES[body.code] : undefined) ?? 'unavailable',
  );
}

function asErrorResponse(body: unknown): ErrorResponse {
  return typeof body === 'object' && body !== null ? body : {};
}
