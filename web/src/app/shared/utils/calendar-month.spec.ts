import {
  addDays,
  addMonths,
  addMonthsKeepingDay,
  calendarDateOf,
  firstDayOfWeekFor,
  localMidnightOf,
  monthOf,
  weekBounds,
  weekdayOf,
  weeksOf,
} from './calendar-month';

describe('calendar-month', () => {
  it('takes today from the browser clock, in its own time zone', () => {
    expect(calendarDateOf(new Date(2026, 9, 7, 23, 59))).toBe('2026-10-07');
    expect(calendarDateOf(new Date(2026, 0, 1, 0, 0))).toBe('2026-01-01');
  });

  it('knows the month of a date', () => {
    expect(monthOf('2026-10-16')).toBe('2026-10');
  });

  it('moves by days across months and years', () => {
    expect(addDays('2026-10-31', 1)).toBe('2026-11-01');
    expect(addDays('2026-01-01', -1)).toBe('2025-12-31');
    expect(addDays('2028-02-28', 1)).toBe('2028-02-29');
  });

  it('moves by months across years', () => {
    expect(addMonths('2026-12', 1)).toBe('2027-01');
    expect(addMonths('2026-01', -1)).toBe('2025-12');
  });

  it('keeps the day of the month, or the last one when the month is shorter', () => {
    expect(addMonthsKeepingDay('2026-10-16', 1)).toBe('2026-11-16');
    expect(addMonthsKeepingDay('2026-01-31', 1)).toBe('2026-02-28');
    expect(addMonthsKeepingDay('2028-03-31', -1)).toBe('2028-02-29');
  });

  it('knows the weekday of a date, with Sunday as 0', () => {
    expect(weekdayOf('2026-10-04')).toBe(0);
    expect(weekdayOf('2026-10-05')).toBe(1);
    expect(weekdayOf('2026-10-10')).toBe(6);
  });

  it('starts the week on Sunday in English and on Monday in Spanish', () => {
    expect(firstDayOfWeekFor('en')).toBe(0);
    expect(firstDayOfWeekFor('en-US')).toBe(0);
    expect(firstDayOfWeekFor('es')).toBe(1);
  });

  it('finds the edges of the week a date falls in', () => {
    expect(weekBounds('2026-10-07', 1)).toEqual({ start: '2026-10-05', end: '2026-10-11' });
    expect(weekBounds('2026-10-07', 0)).toEqual({ start: '2026-10-04', end: '2026-10-10' });
    expect(weekBounds('2026-10-11', 1)).toEqual({ start: '2026-10-05', end: '2026-10-11' });
  });

  it('lays a month out in weeks of seven, with blanks before and after', () => {
    // October 2026 starts on a Thursday and has 31 days.
    const mondayFirst = weeksOf('2026-10', 1);
    expect(mondayFirst.length).toBe(5);
    expect(mondayFirst[0]).toEqual([
      null,
      null,
      null,
      '2026-10-01',
      '2026-10-02',
      '2026-10-03',
      '2026-10-04',
    ]);
    expect(mondayFirst[4]).toEqual([
      '2026-10-26',
      '2026-10-27',
      '2026-10-28',
      '2026-10-29',
      '2026-10-30',
      '2026-10-31',
      null,
    ]);

    const sundayFirst = weeksOf('2026-10', 0);
    expect(sundayFirst[0]?.slice(0, 5)).toEqual([null, null, null, null, '2026-10-01']);
    expect(sundayFirst.every((week) => week.length === 7)).toBeTrue();
  });

  it('lays out a month that fills its weeks exactly', () => {
    // February 2027 starts on a Monday and has 28 days.
    const weeks = weeksOf('2027-02', 1);
    expect(weeks.length).toBe(4);
    expect(weeks.flat()).not.toContain(null);
  });

  it('builds a calendar date at local midnight, so formatting it never shifts the day', () => {
    const midnight = localMidnightOf('2026-10-05');
    expect([midnight.getFullYear(), midnight.getMonth(), midnight.getDate()]).toEqual([2026, 9, 5]);
    expect(midnight.getHours()).toBe(0);
  });
});
