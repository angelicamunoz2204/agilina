/**
 * A date as the person reads it: in the language of the screen, in the time zone of the
 * browser (the API sends instants in UTC; nothing here stores a zone).
 */
export function formatDate(date: Date, locale: string): string {
  return new Intl.DateTimeFormat(locale, { dateStyle: 'long' }).format(date);
}
