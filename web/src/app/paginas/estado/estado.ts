import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';

import { I18nService } from '../../i18n/i18n.service';
import { ApiService, EstadoApi } from '../../nucleo/api.service';

@Component({
  selector: 'agl-estado',
  imports: [],
  templateUrl: './estado.html',
  styleUrl: './estado.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Estado {
  private readonly api = inject(ApiService);
  private readonly i18n = inject(I18nService);

  protected readonly estado = signal<EstadoApi | null>(null);
  protected readonly consultando = signal(false);
  protected readonly error = signal(false);
  protected readonly t = this.i18n.t.bind(this.i18n);

  constructor() {
    this.consultar();
  }

  protected consultar(): void {
    this.consultando.set(true);
    this.error.set(false);

    this.api.salud().subscribe({
      next: (estado) => {
        this.estado.set(estado);
        this.consultando.set(false);
      },
      error: () => {
        this.estado.set(null);
        this.error.set(true);
        this.consultando.set(false);
      },
    });
  }
}
