import { computed, Directive, input } from '@angular/core';

export type ButtonVariant = 'primary' | 'secondary';

const BASE =
  'min-h-11 cursor-pointer rounded-md border px-4 py-2 font-semibold ' +
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-foreground ' +
  'disabled:cursor-progress disabled:opacity-60';

const VARIANTS: Readonly<Record<ButtonVariant, string>> = {
  primary: 'border-accent bg-accent text-background',
  secondary: 'border-border bg-transparent font-normal text-foreground',
};

/**
 * The look of a button. Put it on a native `<button>`, so that keyboard and screen readers
 * keep working: `<button aglButton variant="secondary" type="button">`. Width and spacing
 * belong to whoever places the button (`class="w-full mt-4"`).
 */
@Directive({
  selector: 'button[aglButton]',
  host: { '[class]': 'classes()' },
})
export class Button {
  readonly variant = input<ButtonVariant>('primary');

  protected readonly classes = computed(() => `${BASE} ${VARIANTS[this.variant()]}`);
}
