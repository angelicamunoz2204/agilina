import { TestBed } from '@angular/core/testing';

import { provideTestI18n } from '@testing/i18n';

import { Header } from './header';

describe('Header', () => {
  it('shows the brand and the tagline in the active language', async () => {
    TestBed.configureTestingModule({ imports: [Header], providers: [provideTestI18n()] });
    const fixture = TestBed.createComponent(Header);
    await fixture.whenStable();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelector('.brand')?.textContent).toBe('Agilina');
    expect(element.querySelector('.tagline')?.textContent).toBe(
      'Scrum Master virtual para la reunión diaria',
    );
  });
});
