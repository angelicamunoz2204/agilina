import { TestBed, type ComponentFixture } from '@angular/core/testing';
import { Subject, type Observable } from 'rxjs';

import { provideTestI18n } from '@testing/i18n';

import { StatusPage } from './status-page';
import { HealthPort } from '../application/health.port';
import { type ServiceStatus } from '../domain/service-status';

/** Port double: each check() waits until the test answers it. */
class FakeHealthPort extends HealthPort {
  pending = new Subject<ServiceStatus>();
  calls = 0;

  check(): Observable<ServiceStatus> {
    this.calls++;
    this.pending = new Subject<ServiceStatus>();
    return this.pending;
  }
}

describe('StatusPage', () => {
  let fixture: ComponentFixture<StatusPage>;
  let health: FakeHealthPort;

  beforeEach(() => {
    health = new FakeHealthPort();
    TestBed.configureTestingModule({
      imports: [StatusPage],
      providers: [provideTestI18n(), { provide: HealthPort, useValue: health }],
    });
    fixture = TestBed.createComponent(StatusPage);
    fixture.detectChanges();
  });

  function text(): string {
    return (fixture.nativeElement as HTMLElement).textContent;
  }

  it('says it is checking while the API has not answered', () => {
    expect(text()).toContain('Consultando…');
  });

  it('shows the version reported by the API', async () => {
    health.pending.next({
      service: 'agilina-api',
      version: '0.1.0',
      environment: 'local',
      status: 'alive',
    });
    await fixture.whenStable();

    expect(text()).toContain('Disponible');
    expect(text()).toContain('0.1.0');
  });

  it('warns when the API does not respond and retries on demand', async () => {
    health.pending.error(new Error('No connection'));
    await fixture.whenStable();

    expect(text()).toContain('No disponible');
    (fixture.nativeElement as HTMLElement).querySelector('button')?.click();
    // Not whenStable: the new check stays pending until the test answers it.
    fixture.detectChanges();

    expect(health.calls).toBe(2);
    expect(text()).toContain('Consultando…');
  });
});
