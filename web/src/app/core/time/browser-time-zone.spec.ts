import { TestBed } from '@angular/core/testing';

import { BROWSER_TIME_ZONE } from './browser-time-zone';

describe('BROWSER_TIME_ZONE', () => {
  it('is the IANA time zone the browser resolves', () => {
    const zone = TestBed.inject(BROWSER_TIME_ZONE);

    expect(zone).toBe(Intl.DateTimeFormat().resolvedOptions().timeZone);
    expect(zone).not.toBe('');
  });

  it('can be fixed by a test, whatever machine runs it', () => {
    TestBed.configureTestingModule({
      providers: [{ provide: BROWSER_TIME_ZONE, useValue: 'Asia/Tokyo' }],
    });

    expect(TestBed.inject(BROWSER_TIME_ZONE)).toBe('Asia/Tokyo');
  });
});
