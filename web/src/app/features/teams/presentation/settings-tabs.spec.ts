import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';

import { provideTestI18n } from '@testing/i18n';
import { provideTestTenant } from '@testing/tenant';

import { SettingsTabs } from './settings-tabs';

/** Any section of the settings: it only places the tabs. */
@Component({
  selector: 'agl-test-settings-section',
  imports: [SettingsTabs],
  template: '<agl-settings-tabs teamId="atlas" />',
})
class SettingsSection {}

describe('SettingsTabs', () => {
  let harness: RouterTestingHarness;

  beforeEach(async () => {
    TestBed.configureTestingModule({
      providers: [
        provideTestI18n(),
        provideTestTenant(),
        provideRouter([
          { path: ':tenant/teams/:teamId/settings', component: SettingsSection },
          { path: ':tenant/teams/:teamId/settings/sprint', component: SettingsSection },
        ]),
      ],
    });
    harness = await RouterTestingHarness.create();
  });

  async function open(url: string): Promise<HTMLElement> {
    await harness.navigateByUrl(url);
    await harness.fixture.whenStable();
    return harness.routeNativeElement!;
  }

  function tab(page: HTMLElement, name: string): HTMLAnchorElement {
    const found = Array.from(page.querySelectorAll('nav a')).find(
      (link) => link.textContent.trim() === name,
    );
    expect(found).withContext(`a tab "${name}"`).toBeDefined();
    return found as HTMLAnchorElement;
  }

  it('titles the settings and names its sections, Team and Sprint, and nothing else', async () => {
    const page = await open('/acme/teams/atlas/settings');

    expect(page.querySelector('h1')?.textContent.trim()).toBe('Configuración');
    expect(page.querySelector('nav')?.getAttribute('aria-label')).toBe(
      'Secciones de la configuración',
    );
    expect(Array.from(page.querySelectorAll('nav a')).map((a) => a.textContent.trim())).toEqual([
      'Equipo',
      'Sprint',
    ]);
  });

  it('links each section to its own address in the tenant', async () => {
    const page = await open('/acme/teams/atlas/settings');

    expect(tab(page, 'Equipo').getAttribute('href')).toBe('/acme/teams/atlas/settings');
    expect(tab(page, 'Sprint').getAttribute('href')).toBe('/acme/teams/atlas/settings/sprint');
  });

  it('marks Team as the current page in Settings → Team', async () => {
    const page = await open('/acme/teams/atlas/settings');

    expect(tab(page, 'Equipo').getAttribute('aria-current')).toBe('page');
    expect(tab(page, 'Sprint').hasAttribute('aria-current')).toBeFalse();
  });

  it('marks Sprint as the current page in Settings → Sprint, and only it', async () => {
    const page = await open('/acme/teams/atlas/settings/sprint');

    expect(tab(page, 'Sprint').getAttribute('aria-current')).toBe('page');
    expect(tab(page, 'Equipo').hasAttribute('aria-current')).toBeFalse();
  });

  it('goes to the other section when its tab is followed', async () => {
    const page = await open('/acme/teams/atlas/settings');

    tab(page, 'Sprint').click();
    await harness.fixture.whenStable();

    const sprint = harness.routeNativeElement!;
    expect(tab(sprint, 'Sprint').getAttribute('aria-current')).toBe('page');
  });
});
