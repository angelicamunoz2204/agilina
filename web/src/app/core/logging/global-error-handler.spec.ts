import { TestBed } from '@angular/core/testing';

import { provideFakeLogger, type FakeLogger } from '@testing/fake-logger';

import { GlobalErrorHandler } from './global-error-handler';
import { Logger } from './logger';

describe('GlobalErrorHandler', () => {
  it('logs every unhandled error', () => {
    TestBed.configureTestingModule({ providers: [GlobalErrorHandler, provideFakeLogger()] });
    const logger = TestBed.inject(Logger) as FakeLogger;
    const failure = new Error('boom');

    TestBed.inject(GlobalErrorHandler).handleError(failure);

    expect(logger.entries).toEqual([
      { level: 'error', message: 'Unhandled error', error: failure },
    ]);
  });
});
