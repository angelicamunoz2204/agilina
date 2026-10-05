import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { Button } from './button';

@Component({
  imports: [Button],
  template: `
    <button aglButton type="button" class="w-full">Save</button>
    <button aglButton variant="secondary" type="button">Cancel</button>
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

    expect(cancel?.classList).toContain('bg-transparent');
    expect(cancel?.classList).not.toContain('bg-accent');
  });

  it('stays a native button', () => {
    expect(buttons().map((button) => button.type)).toEqual(['button', 'button']);
  });
});
