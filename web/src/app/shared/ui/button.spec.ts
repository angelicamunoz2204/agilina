import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { Button } from './button';

@Component({
  imports: [Button],
  template: `
    <button aglButton type="button" class="w-full">Save</button>
    <button aglButton variant="secondary" type="button">Cancel</button>
    <a aglButton href="/teams/new">Create</a>
  `,
})
class Host {}

describe('Button', () => {
  function buttons(): HTMLButtonElement[] {
    const fixture = TestBed.createComponent(Host);
    fixture.detectChanges();
    return Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('button'));
  }

  it('is primary unless told otherwise and keeps the classes of its place', () => {
    const [save] = buttons();

    expect(save?.classList).toContain('bg-accent');
    expect(save?.classList).toContain('w-full');
  });

  it('can be secondary', () => {
    const [, cancel] = buttons();

    expect(cancel?.classList).toContain('bg-surface');
    expect(cancel?.classList).not.toContain('bg-accent');
  });

  it('gives a link the look of a button and leaves it a link', () => {
    const fixture = TestBed.createComponent(Host);
    fixture.detectChanges();
    const link = (fixture.nativeElement as HTMLElement).querySelector('a');

    expect(link?.classList).toContain('bg-accent');
    expect(link?.getAttribute('href')).toBe('/teams/new');
  });

  it('stays a native button', () => {
    expect(buttons().map((button) => button.type)).toEqual(['button', 'button']);
  });
});
