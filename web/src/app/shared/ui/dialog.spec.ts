import { Component, signal } from '@angular/core';
import { TestBed, type ComponentFixture } from '@angular/core/testing';

import { Dialog } from './dialog';

@Component({
  imports: [Dialog],
  template: `
    <button type="button" id="opener" (click)="open.set(true)">Open</button>
    @if (open()) {
      <agl-dialog labelledBy="dialog-title" (dismissed)="dismissals = dismissals + 1">
        <h2 id="dialog-title">Title</h2>
        <button type="button" id="inside">Inside</button>
      </agl-dialog>
    }
  `,
})
class Host {
  readonly open = signal(false);
  dismissals = 0;
}

describe('Dialog', () => {
  let fixture: ComponentFixture<Host>;
  let root: HTMLElement;

  beforeEach(async () => {
    fixture = TestBed.createComponent(Host);
    root = fixture.nativeElement as HTMLElement;
    document.body.appendChild(root); // focus only moves inside the document
    await fixture.whenStable();
  });

  afterEach(() => {
    root.remove();
  });

  function dialog(): HTMLDialogElement | null {
    return root.querySelector('dialog');
  }

  async function openFromTheButton(): Promise<HTMLButtonElement> {
    const opener = root.querySelector<HTMLButtonElement>('#opener')!;
    opener.focus();
    opener.click();
    await fixture.whenStable();
    return opener;
  }

  it('opens as a modal when it is placed, named by its title', async () => {
    await openFromTheButton();

    expect(dialog()?.open).toBeTrue();
    expect(dialog()?.matches(':modal')).toBeTrue();
    expect(dialog()?.getAttribute('aria-labelledby')).toBe('dialog-title');
    expect(dialog()?.querySelector('#inside')).not.toBeNull();
  });

  it('gives the focus back to where it was when it is taken away', async () => {
    const opener = await openFromTheButton();
    root.querySelector<HTMLButtonElement>('#inside')!.focus();

    fixture.componentInstance.open.set(false);
    await fixture.whenStable();

    expect(dialog()).toBeNull();
    expect(document.activeElement).toBe(opener);
  });

  it('tells when the browser closed it, as Escape does', async () => {
    await openFromTheButton();

    const closed = new Promise((resolve) => {
      dialog()!.addEventListener('close', resolve, { once: true });
    });
    dialog()!.close();
    await closed; // the browser fires close as a task of its own

    expect(fixture.componentInstance.dismissals).toBe(1);
  });

  it('is not shown while it is not placed', () => {
    expect(dialog()).toBeNull();
  });
});
