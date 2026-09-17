import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { I18nService } from './i18n/i18n.service';

@Component({
  selector: 'agl-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  private readonly i18n = inject(I18nService);

  protected readonly titulo = 'Agilina';
  protected readonly t = this.i18n.t.bind(this.i18n);
}
