import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { provideTestI18n } from '@testing/i18n';

import { App } from './app';

describe('App', () => {
  it('renders the layout around the routed screen', async () => {
    TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([]), provideTestI18n()],
    });
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelector('agl-header')).not.toBeNull();
    expect(element.querySelector('main router-outlet')).not.toBeNull();
  });
});
