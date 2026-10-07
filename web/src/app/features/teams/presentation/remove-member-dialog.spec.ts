import { Component, signal } from '@angular/core';
import { TestBed, type ComponentFixture } from '@angular/core/testing';

import { provideTestI18n } from '@testing/i18n';

import { RemoveMemberDialog } from './remove-member-dialog';
import { type TeamMember } from '../domain/team-member';

@Component({
  imports: [RemoveMemberDialog],
  template: `
    <agl-remove-member-dialog
      [member]="member"
      [saving]="saving()"
      [problem]="problem()"
      (confirmed)="confirmations = confirmations + 1"
      (dismissed)="dismissals = dismissals + 1"
    />
  `,
})
class Host {
  readonly member: TeamMember = {
    userId: 'bruno',
    fullName: 'Bruno Díaz',
    email: 'bruno@example.com',
    role: 'member',
    label: 'member',
    roleChangeBlockedBy: null,
    removalBlockedBy: null,
  };
  readonly saving = signal(false);
  readonly problem = signal<string | null>(null);
  confirmations = 0;
  dismissals = 0;
}

describe('RemoveMemberDialog', () => {
  let fixture: ComponentFixture<Host>;
  let root: HTMLElement;

  beforeEach(async () => {
    TestBed.configureTestingModule({ providers: [provideTestI18n()] });
    fixture = TestBed.createComponent(Host);
    root = fixture.nativeElement as HTMLElement;
    await fixture.whenStable();
  });

  function button(label: string): HTMLButtonElement {
    return Array.from(root.querySelectorAll('button')).find(
      (candidate) => candidate.textContent.trim() === label,
    )!;
  }

  function text(): string {
    return root.textContent.replace(/\s+/g, ' ').trim();
  }

  it('names the person and warns that they stop getting the calls of the team', () => {
    expect(root.querySelector('dialog')?.open).toBeTrue();
    expect(root.querySelector('h2')?.textContent.trim()).toBe('¿Eliminar a Bruno Díaz del equipo?');
    expect(text()).toContain(
      'Bruno Díaz dejará de pertenecer al equipo y de recibir sus convocatorias.',
    );
    expect(text()).toContain(
      'Su cuenta de Agilina no se borra: puede seguir en sus otros equipos.',
    );
  });

  it('tells when the removal is confirmed', () => {
    button('Eliminar del equipo').click();

    expect(fixture.componentInstance.confirmations).toBe(1);
    expect(fixture.componentInstance.dismissals).toBe(0);
  });

  it('tells when it is cancelled', () => {
    button('Cancelar').click();

    expect(fixture.componentInstance.dismissals).toBe(1);
    expect(fixture.componentInstance.confirmations).toBe(0);
  });

  it('cannot be confirmed again while the removal is saving', async () => {
    fixture.componentInstance.saving.set(true);
    await fixture.whenStable();

    expect(button('Eliminando…').disabled).toBeTrue();
  });

  it('cannot be cancelled while the removal is saving', async () => {
    fixture.componentInstance.saving.set(true);
    await fixture.whenStable();
    const escape = new Event('cancel', { cancelable: true });
    root.querySelector('dialog')!.dispatchEvent(escape);

    expect(button('Cancelar').disabled).toBeTrue();
    expect(escape.defaultPrevented).toBeTrue();
  });

  it('announces the problem of the last attempt', async () => {
    fixture.componentInstance.problem.set('problems.last_admin');
    await fixture.whenStable();

    expect(root.querySelector('[role="alert"]')?.textContent.trim()).toBe(
      'No se puede eliminar: el equipo no puede quedarse sin Administrador.',
    );
  });
});
