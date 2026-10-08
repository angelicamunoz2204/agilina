import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { IconButton } from './icon-button';

@Component({
  imports: [IconButton],
  template: `<button aglIconButton type="button" aria-label="Remove" [disabled]="disabled">
    x
  </button>`,
})
class Host {
  disabled = false;
}

describe('IconButton', () => {
  it('styles a native button as a square icon button and keeps it a button', async () => {
    const fixture = TestBed.createComponent(Host);
    await fixture.whenStable();

    const button = (fixture.nativeElement as HTMLElement).querySelector('button')!;
    expect(button.classList).toContain('size-9');
    expect(button.classList).toContain('hover:bg-accent/10');
    expect(button.getAttribute('aria-label')).toBe('Remove');
    expect(button.type).toBe('button');
  });
});
