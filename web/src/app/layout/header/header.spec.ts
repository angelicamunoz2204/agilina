import { TestBed } from '@angular/core/testing';

import { ShellContext } from '@core/shell/shell-context';
import { provideTestI18n } from '@testing/i18n';

import { Header } from './header';

describe('Header', () => {
  async function render(team?: {
    name: string;
    roleLabel: string;
    userName: string;
  }): Promise<HTMLElement> {
    TestBed.configureTestingModule({ imports: [Header], providers: [provideTestI18n()] });
    if (team !== undefined) {
      TestBed.inject(ShellContext).enter(team);
    }
    const fixture = TestBed.createComponent(Header);
    await fixture.whenStable();
    return fixture.nativeElement as HTMLElement;
  }

  it('shows the brand and the tagline in the active language', async () => {
    const element = await render();

    expect(element.textContent).toContain('Agilina');
    expect(element.textContent).toContain('Scrum Master virtual para la reunión diaria');
  });

  it('inside a team shows its name and the label of the role of the user in it', async () => {
    const element = await render({
      name: 'Atlas',
      roleLabel: 'scrum_master',
      userName: 'Ana María Gil',
    });

    expect(element.querySelector('[data-testid=header-team]')?.textContent).toBe('Atlas');
    expect(element.querySelector('[data-testid=header-role-label]')?.textContent.trim()).toBe(
      'Scrum Master',
    );
    expect(element.textContent).not.toContain('reunión diaria');
  });

  it('shows the name of the person and their initials next to the team', async () => {
    const element = await render({
      name: 'Atlas',
      roleLabel: 'scrum_master',
      userName: 'ana maría gil ruiz',
    });

    expect(element.querySelector('[data-testid=header-user-name]')?.textContent.trim()).toBe(
      'ana maría gil ruiz',
    );
    expect(element.querySelector('[data-testid=header-user-initials]')?.textContent.trim()).toBe(
      'AM',
    );
  });

  it('shows no person outside a team', async () => {
    const element = await render();

    expect(element.querySelector('[data-testid=header-user]')).toBeNull();
  });

  it('calls the same admin Administrador once the team is autonomous', async () => {
    const element = await render({ name: 'Nova', roleLabel: 'admin', userName: 'Ana Gil' });

    expect(element.querySelector('[data-testid=header-role-label]')?.textContent.trim()).toBe(
      'Administrador',
    );
  });
});
