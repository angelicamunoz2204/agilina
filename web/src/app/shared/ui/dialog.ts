import {
  afterNextRender,
  Component,
  DOCUMENT,
  type ElementRef,
  inject,
  input,
  type OnDestroy,
  output,
  viewChild,
} from '@angular/core';

/**
 * A modal dialog on the native `<dialog>`, so that the browser traps the focus, makes the rest
 * of the page inert and closes it with Escape. It opens when it is placed and closes when it is
 * taken away, so whoever places it owns whether it is open:
 *
 * ```html
 * @if (inviting()) {
 *   <agl-dialog labelledBy="invite-title" (dismissed)="inviting.set(false)">…</agl-dialog>
 * }
 * ```
 *
 * `dismissed` tells that the person closed it (Escape). With `[dismissible]="false"` (for
 * instance while what it sends is on its way) Escape does nothing. When it goes away, the focus
 * goes back to the element that had it when it opened.
 */
@Component({
  selector: 'agl-dialog',
  templateUrl: './dialog.html',
})
export class Dialog implements OnDestroy {
  /** Id of the element that names the dialog, usually its title. */
  readonly labelledBy = input.required<string>();
  /** Whether Escape closes it; false while the dialog is busy. */
  readonly dismissible = input(true);
  readonly dismissed = output();

  private readonly dialog = viewChild.required<ElementRef<HTMLDialogElement>>('dialog');
  private readonly opener = inject(DOCUMENT).activeElement;
  private readonly opening = afterNextRender(() => {
    this.dialog().nativeElement.showModal();
  });

  ngOnDestroy(): void {
    this.opening.destroy();
    if (this.opener instanceof HTMLElement) {
      this.opener.focus();
    }
  }

  /** Escape asks to close it: refused while it is not dismissible. */
  protected onCancel(event: Event): void {
    if (!this.dismissible()) {
      event.preventDefault();
    }
  }

  /** The browser already closed it (Escape): whoever placed it takes it away. A browser may
   * close it despite the refusal (a second Escape in a row): then it opens again. */
  protected onClose(): void {
    if (this.dismissible()) {
      this.dismissed.emit();
    } else {
      this.dialog().nativeElement.showModal();
    }
  }
}
