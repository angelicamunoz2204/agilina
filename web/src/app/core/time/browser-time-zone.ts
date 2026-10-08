import { InjectionToken } from '@angular/core';

/**
 * The IANA time zone of the browser (`America/Bogota`): the one the daily's time is captured
 * in when an admin saves the sprint (AD-31). A token, so that a test can fix it instead of
 * depending on the machine that runs it.
 */
export const BROWSER_TIME_ZONE = new InjectionToken<string>('BROWSER_TIME_ZONE', {
  providedIn: 'root',
  factory: () => Intl.DateTimeFormat().resolvedOptions().timeZone,
});
