import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { environment } from '../../../../environments/environment';
import { HealthPort } from '../application/health.port';
import { HttpHealthApi } from '../infrastructure/http-health.api';
import { StatusPage } from './status-page';

describe('StatusPage', () => {
  let fixture: ComponentFixture<StatusPage>;
  let http: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [StatusPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: HealthPort, useClass: HttpHealthApi },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(StatusPage);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('shows the version reported by the API', () => {
    fixture.detectChanges();

    http.expectOne(`${environment.apiUrl}/health`).flush({
      service: 'agilina-api',
      version: '0.1.0',
      environment: 'local',
      status: 'alive',
    });
    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.textContent).toContain('0.1.0');
  });

  it('warns when the API does not respond and offers to retry', () => {
    fixture.detectChanges();

    http
      .expectOne(`${environment.apiUrl}/health`)
      .error(new ProgressEvent('error'), { status: 0, statusText: 'No connection' });
    fixture.detectChanges();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelector('.unavailable')).toBeTruthy();
    expect(element.querySelector('button')).toBeTruthy();
  });
});
