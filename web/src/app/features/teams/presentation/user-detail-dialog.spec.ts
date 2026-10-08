import { Component, signal } from '@angular/core';
import { TestBed, type ComponentFixture } from '@angular/core/testing';
import { NEVER, type Observable, of, Subject, throwError } from 'rxjs';

import { provideTestI18n } from '@testing/i18n';

import { UserDetailDialog } from './user-detail-dialog';
import { UsersPort } from '../application/users.port';
import { MemberFailure } from '../domain/member-failure';
import { type RoleOption, type TeamMember } from '../domain/team-member';

const ROW: TeamMember = {
  userId: 'ana',
  fullName: 'Ana Gil',
  email: 'ana@example.com',
  role: 'admin',
  label: 'scrum_master',
  joinedAt: new Date('2026-10-08T12:00:00Z'),
  roleChangeBlockedBy: 'last_admin',
  removalBlockedBy: 'last_admin',
};
const ROLES: RoleOption[] = [
  { role: 'admin', label: 'scrum_master' },
  { role: 'member', label: 'member' },
];

class FakeUsersPort extends UsersPort {
  answer: Observable<TeamMember> = of(ROW);
  readonly asked: [string, string][] = [];

  list(): Observable<never> {
    return NEVER;
  }

  get(teamId: string, userId: string): Observable<TeamMember> {
    this.asked.push([teamId, userId]);
    return this.answer;
  }

  me(): Observable<never> {
    return NEVER;
  }

  invite(): Observable<never> {
    return NEVER;
  }

  changeRole(): Observable<never> {
    return NEVER;
  }

  remove(): Observable<never> {
    return NEVER;
  }
}

@Component({
  imports: [UserDetailDialog],
  template: `
    <agl-user-detail-dialog
      teamId="atlas"
      [member]="row()"
      [roles]="roles"
      (dismissed)="dismissals = dismissals + 1"
    />
  `,
})
class Host {
  readonly row = signal(ROW);
  readonly roles = ROLES;
  dismissals = 0;
}

describe('UserDetailDialog', () => {
  let port: FakeUsersPort;
  let fixture: ComponentFixture<Host>;

  beforeEach(() => {
    port = new FakeUsersPort();
    TestBed.configureTestingModule({
      imports: [Host],
      providers: [provideTestI18n(), { provide: UsersPort, useValue: port }],
    });
  });

  async function open(): Promise<HTMLElement> {
    fixture = TestBed.createComponent(Host);
    await fixture.whenStable();
    return fixture.nativeElement as HTMLElement;
  }

  const text = (page: HTMLElement, id: string): string | undefined =>
    page.querySelector(`[data-testid=${id}]`)?.textContent.trim();

  it('shows who the person is, how the team calls them and since when they are in it', async () => {
    const page = await open();

    expect(text(page, 'user-detail-title')).toBe('Ana Gil');
    expect(text(page, 'user-detail-email')).toBe('ana@example.com');
    expect(text(page, 'user-detail-label')).toBe('Scrum Master');
    expect(text(page, 'user-detail-joined')).toBe('8 de octubre de 2026');
  });

  it('asks the API for the user of the team that opened it', async () => {
    await open();

    expect(port.asked).toEqual([['atlas', 'ana']]);
  });

  it('says why the role cannot change or the user cannot be removed, naming the admin by the label of the team', async () => {
    const page = await open();

    expect(text(page, 'user-detail-role-blocked')).toBe(
      'Es el único Scrum Master: el equipo no puede quedarse sin Scrum Master.',
    );
    expect(text(page, 'user-detail-removal-blocked')).toBe(
      'Es el único Scrum Master: no se puede eliminar del equipo.',
    );
  });

  it('shows the row at once and what the API says once it answers', async () => {
    const answer = new Subject<TeamMember>();
    port.answer = answer;
    // Not whenStable: the request stays pending, so the page never settles.
    fixture = TestBed.createComponent(Host);
    TestBed.tick();
    TestBed.tick();
    const page = fixture.nativeElement as HTMLElement;
    expect(text(page, 'user-detail-title')).toBe('Ana Gil');
    expect(page.textContent).toContain('Cargando…');

    answer.next({ ...ROW, fullName: 'Ana María Gil' });
    answer.complete();
    await fixture.whenStable();

    expect(text(page, 'user-detail-title')).toBe('Ana María Gil');
    expect(page.textContent).not.toContain('Cargando…');
  });

  it('keeps the row and says so when the user cannot be read', async () => {
    port.answer = throwError(() => new MemberFailure('not_found'));

    const page = await open();

    expect(text(page, 'user-detail-title')).toBe('Ana Gil');
    expect(text(page, 'user-detail-problem')).toBe('Esta persona ya no está en el equipo.');
  });

  it('tells that it was closed', async () => {
    const page = await open();

    page.querySelector<HTMLButtonElement>('[data-testid=user-detail-close]')!.click();

    expect(fixture.componentInstance.dismissals).toBe(1);
  });
});
