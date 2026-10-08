import { ApplicationRef, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { NEVER, of, throwError, type Observable } from 'rxjs';

import { ActiveSprintFacade } from './active-sprint.facade';
import { SprintsPort } from './sprints.port';
import { type ActiveSprint } from '../domain/active-sprint';
import { SprintFailure } from '../domain/sprint-failure';

const SPRINT: ActiveSprint = {
  id: 'sprint-1',
  startDate: '2026-10-05',
  endDate: '2026-10-16',
  dailyTime: '2026-10-05T14:00:00Z',
  timeZone: 'America/Bogota',
  nextDailyAt: '2026-10-08T14:00:00Z',
  participants: ['ana'],
  day: { number: 3, total: 12, phase: 'in_progress' },
};

/** Port double: active() answers the sprint of each known team, nothing for 'slow', and refuses the rest. */
class FakeSprintsPort extends SprintsPort {
  readonly read: string[] = [];
  readonly sprints: Record<string, ActiveSprint | null> = { atlas: SPRINT, boreal: null };

  active(teamId: string): Observable<ActiveSprint | null> {
    this.read.push(teamId);
    if (teamId === 'slow') {
      return NEVER;
    }
    const sprint = this.sprints[teamId];
    return sprint === undefined ? throwError(() => new SprintFailure('forbidden')) : of(sprint);
  }

  start(): Observable<never> {
    return NEVER;
  }

  reconfigure(): Observable<never> {
    return NEVER;
  }
}

describe('ActiveSprintFacade', () => {
  let port: FakeSprintsPort;
  let facade: ActiveSprintFacade;

  beforeEach(() => {
    port = new FakeSprintsPort();
    TestBed.configureTestingModule({
      providers: [ActiveSprintFacade, { provide: SprintsPort, useValue: port }],
    });
    facade = TestBed.inject(ActiveSprintFacade);
  });

  async function stable(): Promise<void> {
    await TestBed.inject(ApplicationRef).whenStable();
  }

  it('asks for nothing until it knows which team to follow', async () => {
    await stable();

    expect(port.read).toEqual([]);
    expect(facade.known()).toBeFalse();
    expect(facade.sprint()).toBeNull();
  });

  it('reads the active sprint of the team it follows, with its day', async () => {
    facade.follow(signal('atlas'));
    await stable();

    expect(port.read).toEqual(['atlas']);
    expect(facade.known()).toBeTrue();
    expect(facade.sprint()).toEqual(SPRINT);
  });

  it('knows that a team has no active sprint', async () => {
    facade.follow(signal('boreal'));
    await stable();

    expect(facade.known()).toBeTrue();
    expect(facade.sprint()).toBeNull();
  });

  it('knows nothing while the API has not answered', () => {
    facade.follow(signal('slow'));
    TestBed.tick();

    expect(facade.known()).toBeFalse();
    expect(facade.sprint()).toBeNull();
  });

  it('knows nothing when the API fails, instead of saying the team has no sprint', async () => {
    facade.follow(signal('someone-elses'));
    await stable();

    expect(facade.known()).toBeFalse();
    expect(facade.sprint()).toBeNull();
  });

  it('reads it again when the team id changes', async () => {
    const teamId = signal('atlas');
    facade.follow(teamId);
    await stable();

    teamId.set('boreal');
    await stable();

    expect(port.read).toEqual(['atlas', 'boreal']);
    expect(facade.sprint()).toBeNull();
  });
});
