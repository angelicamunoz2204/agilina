import { Component } from '@angular/core';
import { TestBed, type ComponentFixture } from '@angular/core/testing';

import { PasswordField } from './password-field';
import { TextField } from './text-field';

@Component({
  imports: [PasswordField, TextField],
  template: `
    <label for="secret">Contraseña</label>
    <agl-password-field toggleLabel="Mostrar contraseña">
      <input aglTextField id="secret" type="password" value="a-long-password-1" />
    </agl-password-field>
  `,
})
class Host {}

describe('PasswordField', () => {
  let fixture: ComponentFixture<Host>;
  let root: HTMLElement;

  beforeEach(async () => {
    fixture = TestBed.createComponent(Host);
    root = fixture.nativeElement as HTMLElement;
    await fixture.whenStable();
  });

  function input(): HTMLInputElement {
    return root.querySelector<HTMLInputElement>('#secret')!;
  }

  function toggle(): HTMLButtonElement {
    return root.querySelector<HTMLButtonElement>('agl-password-field button')!;
  }

  it('hides the password until the person asks to see it', () => {
    expect(input().type).toBe('password');
    expect(toggle().getAttribute('aria-pressed')).toBe('false');
  });

  it('is a toggle button with the name it is given, tied to its own box', () => {
    expect(toggle().type).toBe('button');
    expect(toggle().getAttribute('aria-label')).toBe('Mostrar contraseña');
    expect(toggle().getAttribute('aria-controls')).toBe('secret');
  });

  it('shows the password and hides it again, keeping what was typed', async () => {
    toggle().click();
    await fixture.whenStable();

    expect(input().type).toBe('text');
    expect(toggle().getAttribute('aria-pressed')).toBe('true');
    expect(input().value).toBe('a-long-password-1');

    toggle().click();
    await fixture.whenStable();

    expect(input().type).toBe('password');
    expect(toggle().getAttribute('aria-pressed')).toBe('false');
  });

  it('leaves room for the button so that the text never runs under it', () => {
    expect(input().classList).toContain('pr-11');
  });

  it('keeps the label of the box on the box', () => {
    expect(root.querySelector('label')?.htmlFor).toBe(input().id);
  });
});
