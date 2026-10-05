import { TestBed } from '@angular/core/testing';

import { provideTestRuntimeConfig } from '@testing/runtime-config';

import { ConsoleLogger } from './console-logger';

describe('ConsoleLogger', () => {
  function createLogger(logLevel: 'debug' | 'warn'): ConsoleLogger {
    TestBed.configureTestingModule({
      providers: [ConsoleLogger, provideTestRuntimeConfig({ logLevel })],
    });
    return TestBed.inject(ConsoleLogger);
  }

  it('writes a structured entry with a UTC timestamp', () => {
    const write = spyOn(console, 'error');
    const failure = new Error('boom');

    createLogger('debug').error('Request failed', failure, { status: 500 });

    const [line, entry] = write.calls.mostRecent().args as [string, Record<string, unknown>];
    expect(line).toBe('[error] Request failed');
    expect(entry).toEqual(
      jasmine.objectContaining({ level: 'error', error: failure, context: { status: 500 } }),
    );
    expect(entry['timestamp']).toMatch(/Z$/);
  });

  it('drops entries below the configured level', () => {
    const write = spyOn(console, 'info');

    createLogger('warn').info('Not interesting');

    expect(write).not.toHaveBeenCalled();
  });
});
