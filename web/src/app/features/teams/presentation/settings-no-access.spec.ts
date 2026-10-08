import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';

import { provideTestI18n } from '@testing/i18n';
import { provideTestTenant } from '@testing/tenant';

import { SettingsNoAccess } from './settings-no-access';

/** A section of the settings that the API refused: it explains what only an admin does there. */
@Component({
  selector: 'agl-test-refused-section',
  imports: [SettingsNoAccess],
  template: '<agl-settings-no-access teamId="atlas" text="Solo un Administrador puede." />',
})
class RefusedSection {}

describe('SettingsNoAccess', () => {
  let page: HTMLElement;

  beforeEach(async () => {
    TestBed.configureTestingModule({
      providers: [
        provideTestI18n(),
        provideTestTenant(),
        provideRouter([{ path: ':tenant/teams/:teamId/settings', component: RefusedSection }]),
      ],
    });
    const harness = await RouterTestingHarness.create('/acme/teams/atlas/settings');
    await harness.fixture.whenStable();
    page = harness.routeNativeElement!;
  });

  it('says the user has no access, with the title the end-to-end tests look for', () => {
    const title = page.querySelector('[data-testid="settings-forbidden-title"]');

    expect(title?.tagName).toBe('H1');
    expect(title?.textContent.trim()).toBe('No tienes acceso a esta pantalla');
  });

  it('explains what only an admin can do in that section', () => {
    expect(page.querySelector('p')?.textContent.trim()).toBe('Solo un Administrador puede.');
  });

  it('leads back to the dashboard of the team', () => {
    const back = page.querySelector('a');

    expect(back?.textContent.trim()).toBe('Volver al equipo');
    expect(back?.getAttribute('href')).toBe('/acme/teams/atlas');
  });
});
