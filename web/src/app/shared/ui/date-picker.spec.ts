import { Component, signal } from '@angular/core';
import { TestBed, type ComponentFixture } from '@angular/core/testing';

import { DatePicker } from './date-picker';
import { calendarDateOf } from '../utils/calendar-month';

@Component({
  imports: [DatePicker],
  template: `
    <label for="start">Inicio</label>
    <agl-date-picker
      inputId="start"
      testId="start-date"
      describedBy="start-problem"
      placeholder="Elige una fecha"
      previousMonthLabel="Mes anterior"
      nextMonthLabel="Mes siguiente"
      [locale]="locale()"
      [min]="min()"
      [invalid]="invalid()"
      [(value)]="value"
      (touched)="touches.set(touches() + 1)"
    />
    <p id="start-problem">Elige la fecha de inicio.</p>
    <button type="button" id="elsewhere">Otro</button>
  `,
})
class Host {
  readonly value = signal('2026-10-07');
  readonly min = signal('');
  readonly locale = signal('es');
  readonly invalid = signal(false);
  readonly touches = signal(0);
}

describe('DatePicker', () => {
  let fixture: ComponentFixture<Host>;
  let host: Host;
  let root: HTMLElement;

  beforeEach(async () => {
    fixture = TestBed.createComponent(Host);
    host = fixture.componentInstance;
    root = fixture.nativeElement as HTMLElement;
    await fixture.whenStable();
  });

  function box(): HTMLButtonElement {
    return root.querySelector<HTMLButtonElement>('#start')!;
  }

  function dialog(): HTMLElement | null {
    return root.querySelector<HTMLElement>('[role="dialog"]');
  }

  function day(date: string): HTMLButtonElement | null {
    return root.querySelector<HTMLButtonElement>(`button[data-date="${date}"]`);
  }

  function text(element: Element | null): string {
    return element?.textContent.replace(/\s+/g, ' ').trim() ?? '';
  }

  function title(): string {
    return text(root.querySelector('[role="dialog"] h2'));
  }

  async function openCalendar(): Promise<void> {
    box().click();
    await fixture.whenStable();
  }

  async function press(key: string): Promise<void> {
    (document.activeElement ?? root).dispatchEvent(
      new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }),
    );
    await fixture.whenStable();
  }

  it('is a button named by its label that shows the chosen date in words', () => {
    expect(root.querySelector('label')?.htmlFor).toBe('start');
    expect(box().type).toBe('button');
    expect(box().getAttribute('aria-haspopup')).toBe('dialog');
    expect(box().getAttribute('aria-expanded')).toBe('false');
    expect(text(box())).toBe('7 de octubre de 2026');
    expect(box().dataset['value']).toBe('2026-10-07');
    expect(box().dataset['testid']).toBe('start-date');
  });

  it('says what to do while no date is chosen', async () => {
    host.value.set('');
    await fixture.whenStable();

    expect(text(box())).toBe('Elige una fecha');
  });

  it('is described by its own value and by its error, and shows when it is invalid', async () => {
    const described = box().getAttribute('aria-describedby')!.split(' ');
    expect(described).toContain('start-problem');
    expect(described.map((id) => text(root.querySelector(`#${id}`)))).toContain(
      '7 de octubre de 2026',
    );
    expect(box().getAttribute('aria-invalid')).toBe('false');

    host.invalid.set(true);
    await fixture.whenStable();

    expect(box().getAttribute('aria-invalid')).toBe('true');
  });

  it('opens a calendar on the month of the chosen date, with the focus on that day', async () => {
    await openCalendar();

    expect(dialog()).not.toBeNull();
    expect(box().getAttribute('aria-expanded')).toBe('true');
    expect(box().getAttribute('aria-controls')).toBe(dialog()!.id);
    expect(title()).toBe('octubre de 2026');
    expect(document.activeElement).toBe(day('2026-10-07'));
    expect(day('2026-10-07')!.closest('td')!.getAttribute('aria-selected')).toBe('true');
    expect(day('2026-10-07')!.getAttribute('aria-label')).toBe('miércoles, 7 de octubre de 2026');
  });

  it('opens on today when no date is chosen, and marks today', async () => {
    host.value.set('');
    await fixture.whenStable();
    const today = calendarDateOf(new Date());

    await openCalendar();

    expect(document.activeElement).toBe(day(today));
    expect(day(today)!.getAttribute('aria-current')).toBe('date');
  });

  it('starts the week on Monday in Spanish and on Sunday in English', async () => {
    await openCalendar();
    const headers = (): string[] =>
      Array.from(root.querySelectorAll('[role="dialog"] th')).map(
        (header) => header.getAttribute('abbr') ?? '',
      );
    expect(headers()[0]).toBe('lunes');
    expect(headers().length).toBe(7);

    host.locale.set('en');
    await fixture.whenStable();

    expect(headers()[0]).toBe('Sunday');
    expect(title()).toBe('October 2026');
  });

  it('picks a day: keeps the date, closes and gives the focus back to the box', async () => {
    await openCalendar();

    day('2026-10-16')!.click();
    await fixture.whenStable();

    expect(host.value()).toBe('2026-10-16');
    expect(dialog()).toBeNull();
    expect(document.activeElement).toBe(box());
    expect(text(box())).toBe('16 de octubre de 2026');
    expect(host.touches()).toBe(1);
  });

  it('moves between months with its buttons', async () => {
    await openCalendar();

    root.querySelector<HTMLButtonElement>('button[aria-label="Mes siguiente"]')!.click();
    await fixture.whenStable();
    expect(title()).toBe('noviembre de 2026');

    root.querySelector<HTMLButtonElement>('button[aria-label="Mes anterior"]')!.click();
    root.querySelector<HTMLButtonElement>('button[aria-label="Mes anterior"]')!.click();
    await fixture.whenStable();
    expect(title()).toBe('septiembre de 2026');
    // The Tab key still reaches a day of the month on show.
    expect(day('2026-09-01')!.tabIndex).toBe(0);
  });

  it('moves the focus with the keyboard, changing month when it has to', async () => {
    await openCalendar();

    await press('ArrowRight');
    expect(document.activeElement).toBe(day('2026-10-08'));
    await press('ArrowDown');
    expect(document.activeElement).toBe(day('2026-10-15'));
    await press('ArrowUp');
    await press('ArrowLeft');
    expect(document.activeElement).toBe(day('2026-10-07'));
    await press('Home');
    expect(document.activeElement).toBe(day('2026-10-05'));
    await press('End');
    expect(document.activeElement).toBe(day('2026-10-11'));
    await press('PageDown');
    expect(title()).toBe('noviembre de 2026');
    expect(document.activeElement).toBe(day('2026-11-11'));
    await press('PageUp');
    await press('PageUp');
    expect(document.activeElement).toBe(day('2026-09-11'));
  });

  it('closes with Escape without changing the date, and counts as having been there', async () => {
    await openCalendar();
    await press('ArrowRight');

    await press('Escape');

    expect(dialog()).toBeNull();
    expect(host.value()).toBe('2026-10-07');
    expect(document.activeElement).toBe(box());
    expect(host.touches()).toBe(1);
  });

  it('closes when the person opens it again, clicks elsewhere or moves the focus out', async () => {
    await openCalendar();
    await openCalendar();
    expect(dialog()).toBeNull();

    await openCalendar();
    root
      .querySelector('#elsewhere')!
      .dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
    await fixture.whenStable();
    expect(dialog()).toBeNull();

    await openCalendar();
    dialog()!.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true }));
    await fixture.whenStable();
    expect(dialog()).not.toBeNull();

    root.querySelector<HTMLButtonElement>('#elsewhere')!.focus();
    await fixture.whenStable();
    expect(dialog()).toBeNull();
    expect(host.value()).toBe('2026-10-07');
  });

  it('counts leaving the box without opening the calendar as having been there', async () => {
    box().focus();
    root.querySelector<HTMLButtonElement>('#elsewhere')!.focus();
    await fixture.whenStable();

    expect(host.touches()).toBe(1);
  });

  it('shows the days before the minimum but does not let anyone pick them', async () => {
    host.value.set('');
    host.min.set('2026-10-05');
    await fixture.whenStable();

    await openCalendar();
    for (let step = 0; step < 36 && day('2026-10-04') === null; step++) {
      const towards = calendarDateOf(new Date()) < '2026-10-01' ? 'Mes siguiente' : 'Mes anterior';
      root.querySelector<HTMLButtonElement>(`button[aria-label="${towards}"]`)!.click();
      await fixture.whenStable();
    }

    expect(day('2026-10-04')!.getAttribute('aria-disabled')).toBe('true');
    expect(day('2026-10-05')!.getAttribute('aria-disabled')).toBeNull();

    day('2026-10-04')!.click();
    await fixture.whenStable();

    expect(host.value()).toBe('');
    expect(dialog()).not.toBeNull();
  });

  it('opens on the minimum when today is before it', async () => {
    host.value.set('');
    host.min.set('2999-01-15');
    await fixture.whenStable();

    await openCalendar();

    expect(title()).toBe('enero de 2999');
    expect(document.activeElement).toBe(day('2999-01-15'));
  });
});
