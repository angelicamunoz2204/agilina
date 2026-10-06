import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { provideTestI18n } from '@testing/i18n';

import { CenteredLayout } from './centered-layout';

describe('CenteredLayout', () => {
  it('shows the brand and the tagline above the routed screen, without the header', async () => {
    TestBed.configureTestingModule({
      imports: [CenteredLayout],
      providers: [provideRouter([]), provideTestI18n()],
    });
    const fixture = TestBed.createComponent(CenteredLayout);
    await fixture.whenStable();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.textContent).toContain('Agilina');
    expect(element.textContent).toContain('Scrum Master virtual para la reunión diaria');
    expect(element.querySelector('header')).toBeNull();
    expect(element.querySelector('main router-outlet')).not.toBeNull();
  });
});
