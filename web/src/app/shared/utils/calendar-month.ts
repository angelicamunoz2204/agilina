/**
 * Calendar arithmetic on calendar dates (`YYYY-MM-DD`) and months (`YYYY-MM`), the way the
 * API exchanges them. A calendar date has no time zone, so every operation runs in UTC on
 * purpose: the browser's time zone can never move a date to the day before or after.
 */

/** The first day of the week: 0 is Sunday and 1 is Monday, as `Date.getUTCDay` counts. */
export type FirstDayOfWeek = 0 | 1;

/** The calendar date of a moment in the browser's time zone: what "today" is for the person. */
export function calendarDateOf(moment: Date): string {
  return isoDate(moment.getFullYear(), moment.getMonth() + 1, moment.getDate());
}

/** The month (`YYYY-MM`) a calendar date belongs to. */
export function monthOf(date: string): string {
  return date.slice(0, 7);
}

/** The calendar date `days` days after (or before, when negative) `date`. */
export function addDays(date: string, days: number): string {
  const [year, month, day] = parts(date);
  return fromUtc(new Date(Date.UTC(year, month - 1, day + days)));
}

/** The month `months` months after (or before, when negative) `month`. */
export function addMonths(month: string, months: number): string {
  const [year, number] = parts(`${month}-01`);
  return monthOf(fromUtc(new Date(Date.UTC(year, number - 1 + months, 1))));
}

/**
 * The same day of the month `months` months away, or the last day of that month when it is
 * shorter: one month after January 31 is the last day of February.
 */
export function addMonthsKeepingDay(date: string, months: number): string {
  const [, , day] = parts(date);
  const target = addMonths(monthOf(date), months);
  return `${target}-${twoDigits(Math.min(day, daysInMonth(target)))}`;
}

/** The weekday of a calendar date: 0 is Sunday, as `Date.getUTCDay` counts. */
export function weekdayOf(date: string): number {
  const [year, month, day] = parts(date);
  return new Date(Date.UTC(year, month - 1, day)).getUTCDay();
}

/** The first day of the week the person expects: Sunday in English, Monday otherwise. */
export function firstDayOfWeekFor(locale: string): FirstDayOfWeek {
  return locale.toLowerCase().startsWith('en') ? 0 : 1;
}

/** The first and last calendar dates of the week `date` falls in. */
export function weekBounds(
  date: string,
  firstDay: FirstDayOfWeek,
): { readonly start: string; readonly end: string } {
  const start = addDays(date, -((weekdayOf(date) - firstDay + 7) % 7));
  return { start, end: addDays(start, 6) };
}

/**
 * The weeks of a month as a calendar shows them: rows of seven, starting on `firstDay`, with
 * `null` where a cell belongs to the month before or after.
 */
export function weeksOf(month: string, firstDay: FirstDayOfWeek): (string | null)[][] {
  const first = `${month}-01`;
  const leading = (weekdayOf(first) - firstDay + 7) % 7;
  const cells: (string | null)[] = Array.from({ length: leading }, () => null);
  for (let day = 0; day < daysInMonth(month); day++) {
    cells.push(addDays(first, day));
  }
  while (cells.length % 7 !== 0) {
    cells.push(null);
  }
  return [...Array(cells.length / 7).keys()].map((week) => cells.slice(week * 7, week * 7 + 7));
}

/** A calendar date as a local `Date` at midnight, to format it with `Intl` in the browser. */
export function localMidnightOf(date: string): Date {
  const [year, month, day] = parts(date);
  return new Date(year, month - 1, day);
}

function daysInMonth(month: string): number {
  const [year, number] = parts(`${month}-01`);
  return new Date(Date.UTC(year, number, 0)).getUTCDate();
}

function parts(date: string): [number, number, number] {
  const [year = 0, month = 1, day = 1] = date.split('-').map(Number);
  return [year, month, day];
}

function fromUtc(moment: Date): string {
  return isoDate(moment.getUTCFullYear(), moment.getUTCMonth() + 1, moment.getUTCDate());
}

function isoDate(year: number, month: number, day: number): string {
  return `${String(year).padStart(4, '0')}-${twoDigits(month)}-${twoDigits(day)}`;
}

function twoDigits(value: number): string {
  return String(value).padStart(2, '0');
}
