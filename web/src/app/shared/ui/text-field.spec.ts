import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { TextField } from './text-field';

@Component({
  imports: [TextField],
  template: `
    <label for="name">Name</label>
    <input aglTextField id="name" type="text" />
  `,
})
class Host {}

describe('TextField', () => {
  it('styles a native input and leaves its label alone', () => {
    const fixture = TestBed.createComponent(Host);
    fixture.detectChanges();

    const input = (fixture.nativeElement as HTMLElement).querySelector('input');
    expect(input?.classList).toContain('rounded-md');
    expect(input?.id).toBe('name');
    expect(
      (fixture.nativeElement as HTMLElement).querySelector('label[for="name"]'),
    ).not.toBeNull();
  });
});
