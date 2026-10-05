import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { provideTestRuntimeConfig, TEST_RUNTIME_CONFIG } from '@testing/runtime-config';

import { HttpTeamsApi } from './http-teams.api';
import { type Team } from '../domain/team';

describe('HttpTeamsApi', () => {
  const teamsUrl = `${TEST_RUNTIME_CONFIG.apiUrl}/v1/teams`;
  let api: HttpTeamsApi;
  let backend: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        HttpTeamsApi,
        provideHttpClient(),
        provideHttpClientTesting(),
        provideTestRuntimeConfig(),
      ],
    });
    api = TestBed.inject(HttpTeamsApi);
    backend = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    backend.verify();
  });

  it('lists the teams of the user and keeps only their id and name', () => {
    let received: readonly Team[] | undefined;
    api.listMine().subscribe((teams) => (received = teams));

    const request = backend.expectOne(teamsUrl);
    expect(request.request.method).toBe('GET');
    request.flush([
      { id: 'a', name: 'Atlas', role: 'admin' },
      { id: 'b', name: 'Boreal', role: 'member' },
    ]);

    expect(received).toEqual([
      { id: 'a', name: 'Atlas' },
      { id: 'b', name: 'Boreal' },
    ]);
  });

  it('creates a team sending only its name and emits the new id', () => {
    let created: string | undefined;
    api.create('  Atlas  ').subscribe((id) => (created = id));

    const request = backend.expectOne(teamsUrl);
    expect(request.request.method).toBe('POST');
    expect(request.request.body).toEqual({ name: '  Atlas  ' });
    request.flush({ id: 'new-id' }, { status: 201, statusText: 'Created' });

    expect(created).toBe('new-id');
  });

  it('reads one team and maps it to the domain', () => {
    let received: Team | undefined;
    api.get('team-1').subscribe((team) => (received = team));

    const request = backend.expectOne(`${teamsUrl}/team-1`);
    expect(request.request.method).toBe('GET');
    request.flush({ id: 'team-1', name: 'Atlas', mode: 'support', language: 'en', role: 'admin' });

    expect(received).toEqual({ id: 'team-1', name: 'Atlas' });
  });

  it('escapes the team id in the path', () => {
    api.get('a/b').subscribe();

    backend.expectOne(`${teamsUrl}/a%2Fb`).flush({ id: 'a/b', name: 'Atlas' });
  });

  it('lets a refused request fail for the facade to handle', () => {
    let failed = false;
    api.get('someone-elses').subscribe({ error: () => (failed = true) });

    backend
      .expectOne(`${teamsUrl}/someone-elses`)
      .flush({ code: 'not_a_team_member' }, { status: 403, statusText: 'Forbidden' });

    expect(failed).toBeTrue();
  });
});
