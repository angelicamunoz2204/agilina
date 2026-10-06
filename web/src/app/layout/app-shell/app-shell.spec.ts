import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { provideTestI18n } from '@testing/i18n';

import { AppShell } from './app-shell';

describe('AppShell', () => {
  it('puts the header above the routed screen', async () => {
    TestBed.configureTestingModule({
      imports: [AppShell],
      providers: [provideRouter([]), provideTestI18n()],
    });
    const fixture = TestBed.createComponent(AppShell);
    await fixture.whenStable();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelector('header')?.textContent).toContain('Agilina');
    expect(element.querySelector('main router-outlet')).not.toBeNull();
  });
});
