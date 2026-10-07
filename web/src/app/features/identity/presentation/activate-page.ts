import { Component, inject, type OnInit, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { TranslocoDirective } from '@jsverse/transloco';

import { Button } from '@shared/ui/button';
import { PasswordField } from '@shared/ui/password-field';
import { TextField } from '@shared/ui/text-field';

import { ActivationFacade } from '../application/activation.facade';
import { readActivationToken } from '../domain/activation-link';

/**
 * Account activation (`/activate#t=<token>`): the person opens the link from the invitation
 * email, chooses a password and goes on to sign in. The token is read once and then removed
 * from the address bar, so it does not stay in the browser's history or in a screenshot.
 */
@Component({
  selector: 'agl-activate-page',
  imports: [TranslocoDirective, FormsModule, Button, PasswordField, TextField],
  providers: [ActivationFacade],
  templateUrl: './activate-page.html',
})
export class ActivatePage implements OnInit {
  private readonly facade = inject(ActivationFacade);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  protected readonly phase = this.facade.phase;
  protected readonly invitation = this.facade.invitation;
  protected readonly linkProblem = this.facade.linkProblem;
  protected readonly formProblem = this.facade.formProblem;
  protected readonly rejections = this.facade.rejections;
  protected readonly request = this.facade.request;
  protected readonly canRequestNew = this.facade.canRequestNew;
  protected readonly loginFailed = this.facade.loginFailed;

  protected readonly password = signal('');
  protected readonly confirmation = signal('');

  ngOnInit(): void {
    this.facade.open(readActivationToken(this.route.snapshot.fragment));
    // Navigating to the same route without a fragment removes it from the address bar.
    void this.router.navigate([], { relativeTo: this.route, replaceUrl: true });
  }

  protected submit(): void {
    this.facade.activate(this.password(), this.confirmation());
  }

  protected retry(): void {
    this.facade.retry();
  }

  protected requestNew(): void {
    this.facade.requestNew();
  }

  protected goToLogin(): void {
    this.facade.goToLogin();
  }
}
