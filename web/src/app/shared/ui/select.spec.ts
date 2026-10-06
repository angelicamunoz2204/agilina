import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { Select } from './select';

@Component({
  imports: [Select],
  template: `
    <label for="role">Role</label>
    <select aglSelect id="role" class="w-full">
      <option value="admin">Admin</option>
      <option value="member" selected>Member</option>
    </select>
    <select aglSelect id="locked" disabled>
      <option value="admin">Admin</option>
    </select>
  `,
})
class Host {}

describe('Select', () => {
  function render(): HTMLElement {
    const fixture = TestBed.createComponent(Host);
    fixture.detectChanges();
    return fixture.nativeElement as HTMLElement;
  }

  it('styles a native select, keeps the classes of its place and leaves its label alone', () => {
    const root = render();
    const select = root.querySelector<HTMLSelectElement>('#role')!;

    expect(select.classList).toContain('rounded-md');
    expect(select.classList).toContain('w-full');
    expect(select.value).toBe('member');
    expect(root.querySelector('label[for="role"]')).not.toBeNull();
  });

  it('stays a native control that can be disabled', () => {
    const locked = render().querySelector<HTMLSelectElement>('#locked')!;

    expect(locked.tagName).toBe('SELECT');
    expect(locked.disabled).toBeTrue();
    expect(locked.classList).toContain('disabled:opacity-60');
  });
});
