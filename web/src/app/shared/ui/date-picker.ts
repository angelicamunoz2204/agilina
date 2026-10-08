import {
  afterNextRender,
  Component,
  computed,
  ElementRef,
  inject,
  Injector,
  input,
  model,
  output,
  signal,
} from '@angular/core';

import {
  addDays,
  addMonths,
  addMonthsKeepingDay,
  calendarDateOf,
  firstDayOfWeekFor,
  localMidnightOf,
  monthOf,
  weekBounds,
  weeksOf,
} from '../utils/calendar-month';

/** A day cell of the calendar. */
interface CalendarCell {
  readonly date: string;
  readonly day: number;
  readonly name: string;
  readonly selected: boolean;
  readonly today: boolean;
  readonly disabled: boolean;
  /** The classes that tell it apart: chosen, today or neither. */
  readonly tone: string;
}

/** A column header of the calendar: the short name of a weekday, and the full one. */
interface WeekdayHeader {
  readonly short: string;
  readonly long: string;
}

/**
 * A calendar date box (`YYYY-MM-DD`) that opens a calendar of its own, instead of the
 * browser's, which cannot be sized or styled. Its label is a `<label for="…">` pointing at
 * `inputId`, which names the button that opens it:
 *
 * ```html
 * <label for="start-date">Inicio</label>
 * <agl-date-picker inputId="start-date" [locale]="language" [(value)]="startDate"
 *   [placeholder]="t('choose_date')" [previousMonthLabel]="t('previous_month')"
 *   [nextMonthLabel]="t('next_month')" />
 * ```
 *
 * It follows the date picker dialog pattern of the WAI-ARIA practices: the arrows move a day or
 * a week, Page Up and Page Down a month, Home and End to the edges of the week, Enter or Space
 * picks the day and Escape closes it; the focus goes back to the box. Days before `min` show but
 * cannot be picked. Month and weekday names come from `Intl` in `locale`, and the week starts on
 * the day that language expects. `touched` tells that the person left the box, whether or not
 * they picked a day.
 */
@Component({
  selector: 'agl-date-picker',
  templateUrl: './date-picker.html',
  host: {
    class: 'relative block',
    '(document:pointerdown)': 'onDocumentPointerDown($event)',
    '(focusout)': 'onFocusOut($event)',
  },
})
export class DatePicker {
  /** The id of the button that opens the calendar, which its `<label for>` points at. */
  readonly inputId = input.required<string>();
  /** The chosen calendar date, `YYYY-MM-DD`, or empty when there is none. */
  readonly value = model('');
  /** The first date that can be picked, `YYYY-MM-DD`; empty for no limit. */
  readonly min = input('');
  /** The active language, for the names of months and weekdays. */
  readonly locale = input.required<string>();
  /** What the box says while no date is chosen, already translated. */
  readonly placeholder = input.required<string>();
  readonly previousMonthLabel = input.required<string>();
  readonly nextMonthLabel = input.required<string>();
  /** Whether the box shows as invalid (`aria-invalid`). */
  readonly invalid = input(false);
  /** The ids of the elements that describe the box, such as its error message. */
  readonly describedBy = input<string>();
  /** The `data-testid` of the box, for the end-to-end tests. */
  readonly testId = input<string>();
  /** The person left the box, after opening the calendar or not. */
  readonly touched = output();

  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly injector = inject(Injector);
  private readonly today = calendarDateOf(new Date());

  protected readonly open = signal(false);
  /** The month the calendar shows, `YYYY-MM`. */
  protected readonly shownMonth = signal(monthOf(this.today));
  /** The day that holds the keyboard focus inside the calendar. */
  protected readonly focusedDate = signal(this.today);

  /** The one day the Tab key reaches: the focused one, or the 1st when another month shows. */
  protected readonly tabbableDate = computed(() =>
    monthOf(this.focusedDate()) === this.shownMonth()
      ? this.focusedDate()
      : `${this.shownMonth()}-01`,
  );

  protected readonly dialogId = computed(() => `${this.inputId()}-calendar`);
  protected readonly titleId = computed(() => `${this.inputId()}-calendar-title`);
  protected readonly valueId = computed(() => `${this.inputId()}-value`);
  protected readonly describedByIds = computed(() =>
    [this.valueId(), this.describedBy()].filter(Boolean).join(' '),
  );

  private readonly firstDay = computed(() => firstDayOfWeekFor(this.locale()));
  private readonly dayName = computed(
    () => new Intl.DateTimeFormat(this.locale(), { dateStyle: 'full' }),
  );

  /** The chosen date as the person reads it, or empty when there is none. */
  protected readonly displayValue = computed(() =>
    this.value() === ''
      ? ''
      : new Intl.DateTimeFormat(this.locale(), { dateStyle: 'long' }).format(
          localMidnightOf(this.value()),
        ),
  );
  protected readonly monthTitle = computed(() =>
    new Intl.DateTimeFormat(this.locale(), { month: 'long', year: 'numeric' }).format(
      localMidnightOf(`${this.shownMonth()}-01`),
    ),
  );
  protected readonly weekdays = computed<readonly WeekdayHeader[]>(() => {
    const short = new Intl.DateTimeFormat(this.locale(), { weekday: 'short' });
    const long = new Intl.DateTimeFormat(this.locale(), { weekday: 'long' });
    // 2023-12-31 was a Sunday: the week from there, shifted to the first day of the week.
    return [...Array(7).keys()].map((index) => {
      const day = localMidnightOf(addDays('2023-12-31', this.firstDay() + index));
      return { short: short.format(day), long: long.format(day) };
    });
  });
  protected readonly weeks = computed<readonly (CalendarCell | null)[][]>(() =>
    weeksOf(this.shownMonth(), this.firstDay()).map((week) =>
      week.map((date) =>
        date === null
          ? null
          : {
              date,
              day: Number(date.slice(8)),
              name: this.dayName().format(localMidnightOf(date)),
              selected: date === this.value(),
              today: date === this.today,
              disabled: this.isBeforeMin(date),
              tone: toneOf(date === this.value(), date === this.today, this.isBeforeMin(date)),
            },
      ),
    ),
  );

  protected toggle(): void {
    if (this.open()) {
      this.close(true);
      return;
    }
    const start = this.value() !== '' ? this.value() : this.earliestPickable(this.today);
    this.shownMonth.set(monthOf(start));
    this.focusedDate.set(start);
    this.open.set(true);
    this.focusDay();
  }

  protected showMonth(months: number): void {
    this.shownMonth.update((month) => addMonths(month, months));
  }

  protected pick(cell: CalendarCell): void {
    if (cell.disabled) {
      return;
    }
    this.value.set(cell.date);
    this.close(true);
  }

  /** Escape closes the calendar; on a day, the arrows, Page Up/Down, Home and End move. */
  protected onDialogKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      event.preventDefault();
      this.close(true);
      return;
    }
    const onDay = event.target instanceof HTMLElement && event.target.dataset['date'] !== undefined;
    const target = onDay ? this.dateAfterKey(event.key) : null;
    if (target === null) {
      return;
    }
    event.preventDefault();
    this.focusedDate.set(target);
    this.shownMonth.set(monthOf(target));
    this.focusDay();
  }

  /** Leaving the box without opening the calendar counts as having been there. */
  protected onTriggerBlur(): void {
    if (!this.open()) {
      this.touched.emit();
    }
  }

  protected onDocumentPointerDown(event: PointerEvent): void {
    if (this.open() && !this.contains(event.target)) {
      this.close(false);
    }
  }

  protected onFocusOut(event: FocusEvent): void {
    if (this.open() && event.relatedTarget !== null && !this.contains(event.relatedTarget)) {
      this.close(false);
    }
  }

  private dateAfterKey(key: string): string | null {
    const date = this.focusedDate();
    switch (key) {
      case 'ArrowLeft':
        return addDays(date, -1);
      case 'ArrowRight':
        return addDays(date, 1);
      case 'ArrowUp':
        return addDays(date, -7);
      case 'ArrowDown':
        return addDays(date, 7);
      case 'PageUp':
        return addMonthsKeepingDay(date, -1);
      case 'PageDown':
        return addMonthsKeepingDay(date, 1);
      case 'Home':
        return weekBounds(date, this.firstDay()).start;
      case 'End':
        return weekBounds(date, this.firstDay()).end;
      default:
        return null;
    }
  }

  /** Closes the calendar; the focus goes back to the box unless it already went elsewhere. */
  private close(returnFocus: boolean): void {
    this.open.set(false);
    this.touched.emit();
    if (returnFocus) {
      this.trigger()?.focus();
    }
  }

  private focusDay(): void {
    afterNextRender(
      () => {
        this.host.nativeElement
          .querySelector<HTMLButtonElement>(`button[data-date="${this.focusedDate()}"]`)
          ?.focus();
      },
      { injector: this.injector },
    );
  }

  private earliestPickable(date: string): string {
    return this.isBeforeMin(date) ? this.min() : date;
  }

  private isBeforeMin(date: string): boolean {
    return this.min() !== '' && date < this.min();
  }

  private trigger(): HTMLButtonElement | null {
    return this.host.nativeElement.querySelector<HTMLButtonElement>(`#${this.inputId()}`);
  }

  private contains(target: EventTarget | null): boolean {
    return target instanceof Node && this.host.nativeElement.contains(target);
  }
}

function toneOf(selected: boolean, today: boolean, disabled: boolean): string {
  if (selected) {
    return 'bg-accent font-semibold text-accent-foreground';
  }
  const hover = disabled ? '' : ' hover:bg-accent/10';
  return today ? `font-semibold text-accent ring-1 ring-accent${hover}` : hover.trim();
}
