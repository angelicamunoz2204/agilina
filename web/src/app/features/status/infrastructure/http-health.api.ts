import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../../environments/environment';
import { HealthPort } from '../application/health.port';
import { ServiceStatus } from '../domain/service-status';

/** HTTP adapter of the health port: the only exit of this feature towards the API. */
@Injectable()
export class HttpHealthApi extends HealthPort {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  check(): Observable<ServiceStatus> {
    return this.http.get<ServiceStatus>(`${this.baseUrl}/health`);
  }
}
