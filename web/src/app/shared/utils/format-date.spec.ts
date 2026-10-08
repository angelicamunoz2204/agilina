import { formatDate } from './format-date';

describe('formatDate', () => {
  // Noon UTC is the same calendar day in every time zone the tests may run in.
  const date = new Date('2026-10-08T12:00:00Z');

  it('writes the date in Spanish', () => {
    expect(formatDate(date, 'es')).toBe('8 de octubre de 2026');
  });

  it('writes the date in English', () => {
    expect(formatDate(date, 'en')).toBe('October 8, 2026');
  });
});
