import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';

export interface EstadoApi {
  servicio: string;
  version: string;
  entorno: string;
  estado: string;
}

/**
 * Único punto de salida hacia la API.
 *
 * Los controles de la ceremonia no pasan por aquí: viajan por el canal de
 * datos de LiveKit directo al worker.
 */
@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  salud(): Observable<EstadoApi> {
    return this.http.get<EstadoApi>(`${this.base}/salud`);
  }
}
