import { computed, Directive, input } from '@angular/core';

export type ButtonVariant = 'primary' | 'secondary' | 'danger';

const BASE =
  'inline-flex min-h-11 cursor-pointer items-center justify-center gap-2 rounded-md border ' +
  'px-4 py-2 text-sm font-medium transition-colors ' +
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent ' +
  'disabled:cursor-progress disabled:opacity-60';

const VARIANTS: Readonly<Record<ButtonVariant, string>> = {
  primary: 'border-accent bg-accent text-accent-foreground shadow-sm hover:bg-accent/90',
  secondary: 'border-border bg-surface text-foreground shadow-sm hover:bg-accent/5',
  // For what cannot be undone, such as taking someone out of a team.
  danger: 'border-danger bg-danger text-accent-foreground shadow-sm hover:bg-danger/90',
};

/**
 * The look of a button. Put it on a native `<button>`, so that keyboard and screen readers
 * keep working: `<button aglButton variant="secondary" type="button">`. A link that should
 * look like a button stays a link (`<a aglButton routerLink="/teams/new">`): navigating is
 * not acting. Width and spacing belong to whoever places it (`class="w-full mt-4"`).
 */
@Directive({
  selector: 'button[aglButton], a[aglButton]',
  host: { '[class]': 'classes()' },
})
export class Button {
  readonly variant = input<ButtonVariant>('primary');

  protected readonly classes = computed(() => `${BASE} ${VARIANTS[this.variant()]}`);
}
