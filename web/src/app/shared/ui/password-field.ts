import {
  Component,
  computed,
  contentChild,
  effect,
  ElementRef,
  input,
  signal,
} from '@angular/core';

import { TextField } from './text-field';

/**
 * A password box with the button that shows or hides what was typed. It wraps the native
 * `<input aglTextField type="password">`, whose `<label for>` stays next to it:
 *
 * ```html
 * <label for="password">Contraseña</label>
 * <agl-password-field [toggleLabel]="t('show_password')">
 *   <input aglTextField id="password" type="password" autocomplete="new-password" />
 * </agl-password-field>
 * ```
 *
 * The button keeps one name (`toggleLabel`, already translated: "Mostrar contraseña") and says
 * whether it is on with `aria-pressed`, as a toggle button does; `aria-controls` ties it to its
 * own box.
 */
@Component({
  selector: 'agl-password-field',
  templateUrl: './password-field.html',
  host: { class: 'relative block' },
})
export class PasswordField {
  /** The name of the button, already translated. */
  readonly toggleLabel = input.required<string>();
  /** The `data-testid` of the button, for the end-to-end tests. */
  readonly toggleTestId = input<string>();

  private readonly input = contentChild.required(TextField, { read: ElementRef });

  protected readonly visible = signal(false);
  protected readonly inputId = computed(() => (this.input().nativeElement as HTMLInputElement).id);

  private readonly showOrHide = effect(() => {
    const box = this.input().nativeElement as HTMLInputElement;
    box.type = this.visible() ? 'text' : 'password';
    // Room for the button, so that the text never runs under it.
    box.classList.add('pr-11');
  });

  protected toggle(): void {
    this.visible.update((visible) => !visible);
  }
}
