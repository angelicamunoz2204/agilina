import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { map, type Observable } from 'rxjs';

import { RUNTIME_CONFIG } from '@core/config/runtime-config';

import { type HealthPort } from '../application/health.port';
import { type ServiceStatus } from '../domain/service-status';

/** Body of GET /health, exactly as the API sends it. */
interface HealthResponse {
  service: string;
  version: string;
  environment: string;
  status: string;
}

/** HTTP adapter of the health port: the only exit of this feature towards the API. */
@Injectable()
export class HttpHealthApi implements HealthPort {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = inject(RUNTIME_CONFIG).apiUrl;

  check(): Observable<ServiceStatus> {
    return this.http.get<HealthResponse>(`${this.baseUrl}/health`).pipe(map(toServiceStatus));
  }
}

/** The API contract stays in this file; the rest of the app sees the domain model. */
function toServiceStatus(response: HealthResponse): ServiceStatus {
  return {
    service: response.service,
    version: response.version,
    environment: response.environment,
    status: response.status,
  };
}
