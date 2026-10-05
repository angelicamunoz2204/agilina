import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, type Observable } from 'rxjs';

import { RUNTIME_CONFIG } from '@core/config/runtime-config';

import { type TeamsPort } from '../application/teams.port';
import { type Team } from '../domain/team';

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

/** HTTP adapter of the teams port: the only exit of this feature towards the API. */
@Injectable()
export class HttpTeamsApi implements TeamsPort {
  private readonly http = inject(HttpClient);
  private readonly teamsUrl = `${inject(RUNTIME_CONFIG).apiUrl}/v1/teams`;

  listMine(): Observable<readonly Team[]> {
    return this.http.get<MyTeamResponse[]>(this.teamsUrl).pipe(map((teams) => teams.map(toTeam)));
  }

  create(name: string): Observable<string> {
    const body: CreateTeamRequest = { name };
    return this.http
      .post<CreatedTeamResponse>(this.teamsUrl, body)
      .pipe(map((created) => created.id));
  }

  get(teamId: string): Observable<Team> {
    return this.http
      .get<TeamResponse>(`${this.teamsUrl}/${encodeURIComponent(teamId)}`)
      .pipe(map(toTeam));
  }
}

/**
 * The API contract stays in this file; the rest of the app sees the domain model.
 * The role, mode and language are not shown yet, so they do not reach the domain.
 */
function toTeam(response: MyTeamResponse | TeamResponse): Team {
  return { id: response.id, name: response.name };
}
