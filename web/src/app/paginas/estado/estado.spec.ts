import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { environment } from '../../../environments/environment';
import { Estado } from './estado';

describe('Estado', () => {
  let fixture: ComponentFixture<Estado>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Estado],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();

    fixture = TestBed.createComponent(Estado);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('muestra la versión que reporta la API', () => {
    fixture.detectChanges();

    http
      .expectOne(`${environment.apiUrl}/salud`)
      .flush({ servicio: 'agilina-api', version: '0.1.0', entorno: 'local', estado: 'vivo' });
    fixture.detectChanges();

    const elemento = fixture.nativeElement as HTMLElement;
    expect(elemento.textContent).toContain('0.1.0');
  });

  it('avisa cuando la API no responde y ofrece reintentar', () => {
    fixture.detectChanges();

    http
      .expectOne(`${environment.apiUrl}/salud`)
      .error(new ProgressEvent('error'), { status: 0, statusText: 'Sin conexión' });
    fixture.detectChanges();

    const elemento = fixture.nativeElement as HTMLElement;
    expect(elemento.querySelector('.no-disponible')).toBeTruthy();
    expect(elemento.querySelector('button')).toBeTruthy();
  });
});
