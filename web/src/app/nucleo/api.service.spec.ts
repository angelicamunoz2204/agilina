import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../environments/environment';
import { ApiService } from './api.service';

describe('ApiService', () => {
  let servicio: ApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    servicio = TestBed.inject(ApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('consulta la sonda de vida de la API', () => {
    let recibido: string | undefined;
    servicio.salud().subscribe((estado) => (recibido = estado.estado));

    const peticion = http.expectOne(`${environment.apiUrl}/salud`);
    expect(peticion.request.method).toBe('GET');
    peticion.flush({ servicio: 'agilina-api', version: '0.1.0', entorno: 'local', estado: 'vivo' });

    expect(recibido).toBe('vivo');
  });
});
